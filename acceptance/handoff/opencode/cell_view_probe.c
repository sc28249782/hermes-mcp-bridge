#define _GNU_SOURCE
/* FIXTURE ONLY. E creates one inert H; no production/native DB path.
 * Exactly one kernel-written pidfd; no duplicate or reacquired helper handle.
 * Controlled proof-field failures use the SAME original FD for TEST cleanup
 * only AFTER candidate result freeze. This is not production authority. */
#include <linux/sched.h>
#include <sys/syscall.h>
#include <sys/wait.h>
#include <sys/resource.h>
#include <sys/time.h>
#include <unistd.h>
#include <fcntl.h>
#include <poll.h>
#include <signal.h>
#include <errno.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#if !defined(__linux__) || !defined(__x86_64__)
#error "This source is an owned Linux x86_64 fixture only"
#endif

#define SEC INT64_C(1000000000)
static int64_t deadline,cutoff;
static int tracked_helper=-1,helper_signals;
static void expired(int n){(void)n;_exit(89);}
static int64_t now(void){struct timespec t;if(clock_gettime(CLOCK_MONOTONIC,&t))_exit(90);return (int64_t)t.tv_sec*SEC+(int64_t)t.tv_nsec;}
static int arm(int64_t end){
 int64_t n=now();if(n>=end)return 0;int64_t us=(end-n)/1000;if(!us)return 0;
 struct itimerval t={0};t.it_value.tv_sec=(time_t)(us/1000000);t.it_value.tv_usec=(suseconds_t)(us%1000000);
 struct sigaction a={0};a.sa_handler=expired;sigemptyset(&a.sa_mask);
 return !sigaction(SIGALRM,&a,NULL)&&!setitimer(ITIMER_REAL,&t,NULL);
}
static int limits(void){struct rlimit as={268435456,268435456},core={0,0},fds={64,64};return !setrlimit(RLIMIT_AS,&as)&&!setrlimit(RLIMIT_CORE,&core)&&!setrlimit(RLIMIT_NOFILE,&fds);}
static void close_except(int a,int b,int c){for(int fd=3;fd<64;fd++)if(fd!=a&&fd!=b&&fd!=c)close(fd);}
static int ready(int fd,int64_t end){
 struct pollfd p={fd,POLLIN,0};
 for(;;){int64_t n=now();int ms=n>=end?0:(int)((end-n)/1000000);int r=poll(&p,1,ms);
  if(r<0&&errno==EINTR){if(now()>=end)return 0;continue;}
  return r>0&&(p.revents&(POLLIN|POLLHUP));}
}
static int eligible(int fd){siginfo_t s={0};return fd>=0&&!waitid(P_PIDFD,(id_t)fd,&s,WEXITED|WNOHANG|WNOWAIT);}
static int send_owned(int fd,int sig){if(!eligible(fd))return 0;if(ready(fd,now()))return 1;if(fd==tracked_helper)helper_signals++;return !syscall(SYS_pidfd_send_signal,fd,sig,NULL,0)||errno==ESRCH;}
static int reap_exact(int fd,int *repeatable,int *consumed){
 siginfo_t a={0},b={0},c={0};
 if(waitid(P_PIDFD,(id_t)fd,&a,WEXITED|WNOHANG|WNOWAIT)||a.si_pid<=0)return 0;
 if(waitid(P_PIDFD,(id_t)fd,&b,WEXITED|WNOHANG|WNOWAIT)||b.si_pid!=a.si_pid||b.si_code!=a.si_code||b.si_status!=a.si_status)return 0;
 *repeatable=1;
 if(waitid(P_PIDFD,(id_t)fd,&c,WEXITED|WNOHANG)||c.si_pid!=a.si_pid||c.si_code!=a.si_code||c.si_status!=a.si_status)return 0;
 errno=0;*consumed=waitid(P_PIDFD,(id_t)fd,&c,WEXITED|WNOHANG)<0&&errno==ECHILD;
 return *consumed;
}
static int stop_set(int *fds,int count,int *done,int *repeatable,int *consumed){
 int signals[]={SIGTERM,SIGKILL};int64_t waits[]={SEC/5,SEC};
 for(int phase=0;phase<2;phase++){
  for(int i=0;i<count;i++)if(fds[i]>=0&&!done[i]&&!send_owned(fds[i],signals[phase]))return 0;
  int64_t end=now()+waits[phase];if(end>deadline)end=deadline;
  for(int i=0;i<count;i++)if(fds[i]>=0&&!done[i]&&ready(fds[i],end))done[i]=reap_exact(fds[i],&repeatable[i],&consumed[i]);
  int all=1;for(int i=0;i<count;i++)if(fds[i]>=0&&!done[i])all=0;if(all)return 1;
 }
 return 0;
}
static int eof_now(int fd,size_t cap){
 size_t total=0;char buf[4096];
 for(;;){ssize_t n=read(fd,buf,sizeof(buf));if(n==0)return 1;if(n<0)return (errno==EAGAIN||errno==EWOULDBLOCK)?0:-1;
  total+=(size_t)n;if(total>cap)return -1;}
}
static int eof_until(int fd,size_t cap){
 size_t total=0;char buf[4096];
 for(;;){if(!ready(fd,deadline))return 0;ssize_t n=read(fd,buf,sizeof(buf));if(n==0)return 1;
  if(n<0){if(errno==EINTR||errno==EAGAIN)continue;return 0;}total+=(size_t)n;if(total>cap)return 0;}
}

/* CLOSED owned fixture. The admission tuple is local test data, NOT an issuer. */
enum { UNATTEMPTED, CREATING, BOUND_UNPUBLISHED, COMMITTED, VIEW_INVALID, TERMINAL };
struct tuple { int attempt,generation,source,role,fdmap; int64_t d,outer; };
struct cell { int fd,consumed,closed,revoked,reaped; pid_t creator; struct tuple binding; };
struct view { int marker,slot,version; struct tuple binding; };
static struct tuple admission;
static int restore_calls,target_calls,post_fault_targets;
static int allowed(struct cell *c) {
 return c->fd>=0 && c->consumed && !c->closed && !c->revoked && !c->reaped
  && c->creator==getpid() && !memcmp(&c->binding,&admission,sizeof(admission))
  && now()<deadline && eligible(c->fd);
}
static int view_valid(struct cell *c,struct view *v) {
 return allowed(c) && v->marker==1 && v->slot==0 && v->version==1
  && !memcmp(&v->binding,&admission,sizeof(admission));
}
static int rebuild(struct cell *c,struct view *v,const struct tuple *request) {
 if(restore_calls++)return 0; /* one attempt, including rejected restore */
 if(now()>=cutoff || memcmp(request,&admission,sizeof(admission)) || !allowed(c))return 0;
 struct view next={0};next.slot=0;next.version=1;next.binding=c->binding;
 next.marker=1;*v=next;return view_valid(c,v);
}
static int candidate_cleanup(struct cell *c,int *repeat,int *consumed) {
 /* No target syscall if proof is invalid. Closing gate occurs separately. */
 if(!allowed(c))return 0;
 target_calls++;
 int f[]={c->fd},done[]={0},rep[]={0},con[]={0};
 int ok=stop_set(f,1,done,rep,con)&&done[0];
 *repeat=rep[0];*consumed=con[0];if(ok)c->reaped=1;return ok;
}
static void inert_child(int gate,int out,int err,int event) {
 if(!limits()||!arm(deadline))_exit(91);
 signal(SIGTERM,SIG_IGN);
 int f[]={fcntl(gate,F_DUPFD_CLOEXEC,10),fcntl(out,F_DUPFD_CLOEXEC,10),fcntl(err,F_DUPFD_CLOEXEC,10)};
 for(int i=0;i<3;i++)if(f[i]<0||dup2(f[i],i)<0)_exit(92);
 close_except(event,-1,-1);
 if(write(event,"B",1)!=1)_exit(93);
 close(event);char ch;ssize_t n;
 do {n=read(0,&ch,1);}while(n<0&&errno==EINTR);
 _exit(n==0?0:94); /* no G byte is ever written */
}
static int no_children(void) {
 /* TEST oracle local to E, not a host inventory or recovery path. */
 siginfo_t s={0};errno=0;
 return waitid(P_ALL,0,&s,WEXITED|WNOHANG|WNOWAIT)<0&&errno==ECHILD;
}
static const char *jb(int x){return x?"true":"false";}
static int valid_mode(const char *m) {
 const char *modes[]={"normal","view_erased","restore_twice","before_publish","partial_publish","stale_publish",
 "wrong_generation","revoked","closed_reused","cell_corrupt","closed_handle","deadline_guard"};
 for(unsigned i=0;i<sizeof(modes)/sizeof(*modes);i++)if(!strcmp(m,modes[i]))return 1;
 return 0;
}
struct result {int known,reaped,repeat,consumed,out_eof,err_eof,cleanup;};
int main(int argc,char **argv) {
 if(argc!=3||!valid_mode(argv[1]))return 2;
 char *end;errno=0;long long input=strtoll(argv[2],&end,10);
 if(errno||!*argv[2]||*end)return 2;
 int64_t t0=(int64_t)input,ta=now();
 if(t0>INT64_MAX-45*SEC||ta>INT64_MAX-20*SEC)return 2;
 int64_t outer=t0+45*SEC;deadline=ta+8*SEC;if(deadline>outer)deadline=outer;cutoff=deadline-3*SEC;
 const char *mode=argv[1],*status="HOLD",*availability="NOT_PROBED";
 int g[2]={-1,-1},o[2]={-1,-1},e[2]={-1,-1},b[2]={-1,-1},spare[2]={-1,-1};
 struct cell c={.fd=-1};struct view v={0};struct result result={0},frozen={0};
 int create_calls=0,initial_commit=0,restore_ok=0,second_denied=0,publish_rejected=0;
 int reused=0,closed_after_reap=0,diagnostic=0,diag_live=0,diag_reaped=0,diag_eof=0;
 int candidate_before_diag=0,consumed_slot=0,phase=UNATTEMPTED,within=0,none=0;
 if(!limits())return 3;
 struct sigaction a={0},actual={0};a.sa_handler=SIG_DFL;sigemptyset(&a.sa_mask);
 if(sigaction(SIGCHLD,&a,NULL)||sigaction(SIGCHLD,NULL,&actual)||actual.sa_handler!=SIG_DFL||(actual.sa_flags&SA_NOCLDWAIT))return 3;
 if(ta<t0||deadline-ta<=3*SEC){status="BUDGET_REJECTED";goto finish;}
 if(!arm(outer))return 3;
 if(pipe2(g,O_CLOEXEC)||pipe2(o,O_CLOEXEC)||pipe2(e,O_CLOEXEC)||pipe2(b,O_CLOEXEC))return 3;
 if(fcntl(o[0],F_SETFL,O_NONBLOCK)||fcntl(e[0],F_SETFL,O_NONBLOCK))return 3;
 /* Static fixture tuple; no production issuer/source attestation is claimed. */
 memset(&admission,0,sizeof(admission));admission.attempt=1;admission.generation=11;
 admission.source=17;admission.role=3;admission.fdmap=1;admission.d=deadline;admission.outer=outer;
 c.binding=admission;c.creator=getpid();c.consumed=1;consumed_slot=1;phase=CREATING;
 struct clone_args args={0};args.flags=CLONE_PIDFD;args.exit_signal=SIGCHLD;args.pidfd=(uint64_t)(uintptr_t)&c.fd;
 create_calls++;long birth=syscall(SYS_clone3,&args,sizeof(args));int birth_errno=errno;
 if(birth==0)inert_child(g[0],o[1],e[1],b[1]);
 if(birth<0){
  if(birth_errno==ENOSYS||birth_errno==EPERM||birth_errno==EACCES||birth_errno==EOPNOTSUPP){availability="UNSUPPORTED";status="UNSUPPORTED";}
  else status="CREATE_UNCONFIRMED";
  goto finish;
 }
 /* Numeric birth return is never retained or used as a target. */
 birth=-1;availability="SUPPORTED";phase=BOUND_UNPUBLISHED;tracked_helper=c.fd;
 close(g[0]);g[0]=-1;close(o[1]);o[1]=-1;close(e[1]);e[1]=-1;close(b[1]);b[1]=-1;
 if(!ready(b[0],cutoff))return 4;
 char ch;if(read(b[0],&ch,1)!=1||ch!='B')return 4;
 /* Named publication faults occur BEFORE any valid binding publication. */
 if(strcmp(mode,"before_publish")){
  v.slot=0;v.version=1;v.binding=admission;
  if(!strcmp(mode,"partial_publish"))v.binding.source++;
  if(!strcmp(mode,"stale_publish"))v.binding.generation--;
  v.marker=1;
 }
 initial_commit=view_valid(&c,&v);if(initial_commit)phase=COMMITTED;
 if(!strcmp(mode,"before_publish")||!strcmp(mode,"partial_publish")||!strcmp(mode,"stale_publish")){
  publish_rejected=!view_valid(&c,&v);phase=VIEW_INVALID;status="PUBLICATION_REJECTED";
 }
 if(!strcmp(mode,"view_erased")||!strcmp(mode,"restore_twice")||!strcmp(mode,"wrong_generation")||!strcmp(mode,"revoked")){
  memset(&v,0,sizeof(v));phase=VIEW_INVALID;struct tuple request=admission;
  if(!strcmp(mode,"wrong_generation"))request.generation--;
  if(!strcmp(mode,"revoked"))c.revoked=1;
  restore_ok=rebuild(&c,&v,&request);
  if(!strcmp(mode,"restore_twice"))second_denied=!rebuild(&c,&v,&request);
  status=restore_ok?"VIEW_REBUILT_CLEANUP_ONLY":"RESTORE_REJECTED";
 }
 if(!strcmp(mode,"cell_corrupt")){c.binding.source++;memset(&v,0,sizeof(v));phase=VIEW_INVALID;status="CELL_PROOF_LOST";}
 if(!strcmp(mode,"closed_reused")||!strcmp(mode,"closed_handle")){
  close(g[1]);g[1]=-1;int rep=0,con=0;
  if(!candidate_cleanup(&c,&rep,&con))return 4;
  closed_after_reap=c.reaped;
  if(pipe2(spare,O_CLOEXEC))return 4; /* unrelated owned pipe, never another pidfd */
  c.closed=1;close(c.fd);
  if(!strcmp(mode,"closed_reused")){
   if(dup2(spare[1],c.fd)!=c.fd)return 4;
   char mark='X',seen=0;
   if(write(c.fd,&mark,1)!=1||read(spare[0],&seen,1)!=1||seen!=mark)return 4;
   reused=1;
  }
  phase=VIEW_INVALID;status="HANDLE_LOST";
 }
 if(!strcmp(mode,"normal"))status="BOUND_FIXTURE_ONLY";
 {
  int before=target_calls;
  if(!strcmp(mode,"cell_corrupt")||!strcmp(mode,"revoked")||!strcmp(mode,"wrong_generation")){
   /* Freeze rejection while H is still live; invalid request cannot permit cleanup. */
   if(!strcmp(mode,"wrong_generation"))c.revoked=1; /* conservative attempt abort */
  }else if(g[1]>=0){close(g[1]);g[1]=-1;}
  result.known=allowed(&c);
  result.reaped=candidate_cleanup(&c,&result.repeat,&result.consumed);
  if(phase==VIEW_INVALID&&!result.known)post_fault_targets=target_calls-before;
  result.out_eof=eof_now(o[0],65536)==1;result.err_eof=eof_now(e[0],4096)==1;
  if(result.reaped){result.out_eof=eof_until(o[0],65536);result.err_eof=eof_until(e[0],4096);}
  result.cleanup=result.known&&result.reaped&&result.out_eof&&result.err_eof;
  candidate_before_diag=result.cleanup;
 }
 memcpy(&frozen,&result,sizeof(result));
 if(!result.cleanup&&!closed_after_reap){
  /* TEST ONLY cleanup of same original FD; no duplicate, reacquire, cell repair or new grant.
   * Only controlled proof-field/revocation faults occur: the live FD field was not lost/closed. */
  diagnostic=1;diag_live=!ready(c.fd,now());
  if(g[1]>=0){close(g[1]);g[1]=-1;}
  int f[]={c.fd},done[]={0},rep[]={0},con[]={0};
  diag_reaped=stop_set(f,1,done,rep,con)&&done[0];
  diag_eof=eof_until(o[0],65536)&&eof_until(e[0],4096);
 }
 if(memcmp(&frozen,&result,sizeof(result)))return 5;
 phase=TERMINAL;
finish:
 none=no_children();
 int fds[]={g[0],g[1],o[0],o[1],e[0],e[1],b[0],b[1],spare[0],spare[1]};
 for(unsigned i=0;i<sizeof(fds)/sizeof(*fds);i++)if(fds[i]>=0)close(fds[i]);
 if(c.fd>=0&&(!c.closed||reused))close(c.fd);
 within=now()<deadline;
 printf("{\"kind\":\"cell-view-result\",\"state\":\"UNKNOWN\",\"status\":\"%s\",\"availability\":\"%s\",\"create_calls\":%d,\"slot_consumed\":%s,\"initial_commit\":%s,\"restore_calls\":%d,\"restore_ok\":%s,\"second_restore_denied\":%s,\"publication_rejected\":%s,\"fd_reused\":%s,\"closed_after_exact_reap\":%s,\"post_fault_target_calls\":%d,\"candidate\":{\"binding_known\":%s,\"helper_reaped\":%s,\"wnowait_repeatable\":%s,\"wait_consumed\":%s,\"stdout_eof\":%s,\"stderr_eof\":%s,\"cleanup_confirmed\":%s},\"diagnostic\":{\"used\":%s,\"h_live_before\":%s,\"exact_reap\":%s,\"both_eof\":%s},\"candidate_result_frozen\":%s,\"no_children\":%s,\"within_original_deadline\":%s,\"terminal\":%s,\"production_feasible\":false,\"profile_selected\":false,\"capture_allowed\":false,\"authorizes_actions\":false,\"dev_observed\":false,\"goal_verified\":false,\"full_atomicity_proven\":false}\n",
 status,availability,create_calls,jb(consumed_slot),jb(initial_commit),restore_calls,jb(restore_ok),jb(second_denied),jb(publish_rejected),jb(reused),jb(closed_after_reap),post_fault_targets,
 jb(result.known),jb(result.reaped),jb(result.repeat),jb(result.consumed),jb(result.out_eof),jb(result.err_eof),jb(result.cleanup),
 jb(diagnostic),jb(diag_live),jb(diag_reaped),jb(diag_eof),jb(candidate_before_diag==result.cleanup),jb(none),jb(within),jb(phase==TERMINAL));
 return none&&within?0:6;
}
