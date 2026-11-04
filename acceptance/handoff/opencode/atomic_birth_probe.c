#define _GNU_SOURCE
/* FIXTURE ONLY. E directly creates inert R/H; no production/native DB path.
 * Candidate uses ONLY kernel-written pidfd slots, never returned PID targets.
 * Diagnostic duplicate handles are test-only and used AFTER result freeze. */
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
static volatile sig_atomic_t noticed;
static int tracked_helper=-1,helper_signals;
static void expired(int n){(void)n;_exit(89);}
static void notice(int n){(void)n;noticed=1;}
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
static void child(int role,int gate,int out,int err,int event,const char *mode){
 if(!limits()||!arm(deadline))_exit(91);
 signal(SIGTERM,SIG_IGN);
 if(role==0){close_except(-1,-1,-1);for(;;)pause();}
 int f[]={fcntl(gate,F_DUPFD_CLOEXEC,10),fcntl(out,F_DUPFD_CLOEXEC,10),fcntl(err,F_DUPFD_CLOEXEC,10)};
 for(int i=0;i<3;i++)if(f[i]<0||dup2(f[i],i)<0)_exit(92);
 close_except(event,-1,-1);
 if(write(event,"B",1)!=1)_exit(93);
 close(event);
 if(!strcmp(mode,"early_exit"))_exit(0);
 if(!strcmp(mode,"erase_copyout")||!strcmp(mode,"close_copyout"))for(;;)pause();
 char ch;ssize_t n;do{n=read(0,&ch,1);}while(n<0&&errno==EINTR);
 _exit(n==0?0:94);  /* gate is NEVER opened for protected work in this probe */
}
struct slot{int pidfd,attempted,copyout,discarded;volatile long returned_pid;};
static long create_slot(struct slot *s,int role,int gate,int out,int err,int event,const char *mode,int bad_address){
 if(s->attempted){errno=EALREADY;return -1;}s->attempted=1;s->pidfd=-1;
 if(now()>=cutoff){errno=ETIMEDOUT;return -1;}
 struct clone_args a={0};a.flags=CLONE_PIDFD;a.exit_signal=SIGCHLD;
 a.pidfd=bad_address?1:(uint64_t)(uintptr_t)&s->pidfd;
 volatile long returned=syscall(SYS_clone3,&a,sizeof(a));
 if(returned==0)child(role,gate,out,err,event,mode);
 if(returned>0){
  s->copyout=s->pidfd>=0&&(fcntl(s->pidfd,F_GETFD)&FD_CLOEXEC)!=0;
  s->returned_pid=returned;
  if(role==1&&(!strcmp(mode,"forget_pid")||!strcmp(mode,"r_loss_forget_pid")||!strcmp(mode,"signal_flag")||!strcmp(mode,"erase_copyout")||!strcmp(mode,"close_copyout"))){s->returned_pid=-1;s->discarded=1;}
  /* No target operation uses the numeric return, retained or forgotten. */
  returned=-1;
  return s->copyout?1:-2;
 }
 return -1;
}
static const char *json_bool(int x){return x?"true":"false";}
struct outcome{int known,reaped,stdout_eof,stderr_eof,confirmed,unknown,wnowait,consumed;};
static int harness_no_children(void){
 /* TEST oracle only, not inventory or a candidate cleanup mechanism. */
 siginfo_t s={0};errno=0;return waitid(P_ALL,0,&s,WEXITED|WNOHANG|WNOWAIT)<0&&errno==ECHILD;
}
static int valid_case(const char *m){const char *cases[]={"normal","forget_pid","r_loss","r_loss_forget_pid","signal_flag","early_exit","bad_copyout","fd_exhaustion","erase_copyout","close_copyout","sigchld_ignore","sigchld_nocldwait","repeat_slot","deadline_guard"};for(unsigned i=0;i<sizeof(cases)/sizeof(*cases);i++)if(!strcmp(m,cases[i]))return 1;return 0;}
int main(int argc,char **argv){
 if(argc!=3||!valid_case(argv[1]))return 2;
 char *end;errno=0;long long input=strtoll(argv[2],&end,10);if(errno||!*argv[2]||*end)return 2;
 int64_t t0=(int64_t)input,ta=now();if(t0>INT64_MAX-45*SEC||ta>INT64_MAX-20*SEC)return 2;
 const char *mode=argv[1],*availability="NOT_PROBED",*status="HOLD",*kernel_error="NONE";
 int sig_ok=0,case_ran=0,kernel_copyout=0,attempts=0,r_reaped=0,diag_used=0,diag_live=0,diag_reaped=0,diag_eof=0;
 int no_children=0,all_clean=0,slot_repeat_denied=0;
 int gate[2]={-1,-1},out[2]={-1,-1},err[2]={-1,-1},event[2]={-1,-1};
 int diag_fd=-1,original_erased=-1;
 struct slot r={.pidfd=-1},h={.pidfd=-1};struct outcome result={0},frozen={0};
 int done[2]={0,0},rep[2]={0,0},cons[2]={0,0};
 int64_t outer=t0+45*SEC;deadline=ta+8*SEC;if(deadline>outer)deadline=outer;
 cutoff=deadline-3*SEC;
 if(!limits())return 3;
 struct sigaction setup={0},actual={0};setup.sa_handler=SIG_DFL;sigemptyset(&setup.sa_mask);
 if(!strcmp(mode,"sigchld_ignore"))setup.sa_handler=SIG_IGN;
 if(!strcmp(mode,"sigchld_nocldwait"))setup.sa_flags=SA_NOCLDWAIT;
 if(sigaction(SIGCHLD,&setup,NULL)||sigaction(SIGCHLD,NULL,&actual))return 3;
 sig_ok=actual.sa_handler==SIG_DFL&&!(actual.sa_flags&SA_NOCLDWAIT);
 if(!sig_ok){status="SIGCHLD_REJECTED";case_ran=1;goto finish;}
 if(ta<t0||ta>=outer||deadline<=ta||deadline-ta<=3*SEC){status="BUDGET_REJECTED";case_ran=1;goto finish;}
 if(!arm(outer))return 3;
 if(pipe2(gate,O_CLOEXEC)||pipe2(out,O_CLOEXEC)||pipe2(err,O_CLOEXEC)||pipe2(event,O_CLOEXEC))goto finish;
 if(fcntl(out[0],F_SETFL,O_NONBLOCK)||fcntl(err[0],F_SETFL,O_NONBLOCK))goto finish;
 attempts++;long rr=create_slot(&r,0,-1,-1,-1,-1,mode,0);int rerrno=errno;
 if(rr<0){
  if(rerrno==ENOSYS||rerrno==EPERM||rerrno==EACCES||rerrno==EOPNOTSUPP){availability="UNSUPPORTED";status="UNSUPPORTED";kernel_error=rerrno==ENOSYS?"ENOSYS":"DENIED";}
  else{status="CREATE_UNCONFIRMED";kernel_error="OTHER";}
  goto cleanup;
 }
 availability="SUPPORTED";
 int filled[64],nf=0;
 if(!strcmp(mode,"fd_exhaustion")){
  for(;;){int f=fcntl(0,F_DUPFD_CLOEXEC,3);if(f<0)break;if(nf>=64){close(f);return 3;}filled[nf++]=f;}
  if(errno!=EMFILE)return 3;
 }
 attempts++;long hr=create_slot(&h,1,gate[0],out[1],err[1],event[1],mode,!strcmp(mode,"bad_copyout"));int herrno=errno;
 for(int i=0;i<nf;i++)close(filled[i]);
 if(!strcmp(mode,"fd_exhaustion")){
  case_ran=1;status="FD_EXHAUSTION_UNCONFIRMED";kernel_error=herrno==EMFILE?"EMFILE":"OTHER";
  if(hr>=0)status="UNEXPECTED_FD_SUCCESS";
  goto cleanup;
 }
 if(!strcmp(mode,"bad_copyout")){
  case_ran=1;status="COPYOUT_ERROR_UNCONFIRMED";kernel_error=herrno==EFAULT?"EFAULT":"OTHER";
  if(hr>=0){status="UNEXPECTED_COPYOUT_SUCCESS";}
  goto cleanup;
 }
 if(hr<0){status="CREATE_UNCONFIRMED";goto cleanup;}
 kernel_copyout=h.copyout;
 tracked_helper=h.pidfd;
 /* All cases intentionally avoid retaining/using numeric returned PID targets. */
 case_ran=1;
 close(event[1]);event[1]=-1;
 if(!ready(event[0],cutoff)){status="CHILD_READY_UNCONFIRMED";goto cleanup;}
 char b;if(read(event[0],&b,1)!=1||b!='B'){status="CHILD_READY_UNCONFIRMED";goto cleanup;}
 if(!strcmp(mode,"early_exit")&&!ready(h.pidfd,cutoff)){status="EXIT_UNCONFIRMED";goto cleanup;}
 if(!strcmp(mode,"r_loss")||!strcmp(mode,"r_loss_forget_pid")){
  if(!send_owned(r.pidfd,SIGKILL)||!ready(r.pidfd,deadline)){status="R_LOSS_UNCONFIRMED";goto cleanup;}
 }
 if(!strcmp(mode,"signal_flag")){
  struct sigaction u={0};u.sa_handler=notice;sigemptyset(&u.sa_mask);
  if(sigaction(SIGUSR1,&u,NULL)||raise(SIGUSR1)||!noticed){status="SIGNAL_UNCONFIRMED";goto cleanup;}
 }
 if(!strcmp(mode,"repeat_slot")){
  errno=0;long again=create_slot(&h,1,gate[0],out[1],err[1],event[0],mode,0);
  slot_repeat_denied=again<0&&errno==EALREADY;if(!slot_repeat_denied){status="SLOT_REUSED";goto cleanup;}
 }
 if(!strcmp(mode,"erase_copyout")||!strcmp(mode,"close_copyout")){
  /* TEST ONLY extra capability, never read by candidate cleanup below. */
  diag_fd=fcntl(h.pidfd,F_DUPFD_CLOEXEC,3);if(diag_fd<0){status="DIAGNOSTIC_UNAVAILABLE";goto cleanup;}
  original_erased=h.pidfd;
  if(!strcmp(mode,"close_copyout")){close(original_erased);original_erased=-1;}
  h.pidfd=-1;status="COPYOUT_METADATA_LOST";
 }else status="KERNEL_COPYOUT_OBSERVED";
cleanup:
 if(gate[1]>=0){close(gate[1]);gate[1]=-1;}
 if(out[1]>=0){close(out[1]);out[1]=-1;}
 if(err[1]>=0){close(err[1]);err[1]=-1;}
 {
  int f[]={r.pidfd,h.pidfd};all_clean=stop_set(f,2,done,rep,cons);r_reaped=done[0];
  result.known=h.pidfd>=0;result.reaped=done[1];result.unknown=h.attempted&&h.pidfd<0;
  result.wnowait=rep[1];result.consumed=cons[1];
  if(out[0]>=0)result.stdout_eof=result.unknown?eof_now(out[0],65536):eof_until(out[0],65536);
  if(err[0]>=0)result.stderr_eof=result.unknown?eof_now(err[0],4096):eof_until(err[0],4096);
  result.confirmed=all_clean&&r_reaped&&h.pidfd>=0&&!result.unknown&&result.stdout_eof==1&&result.stderr_eof==1;
 }
 memcpy(&frozen,&result,sizeof(result));
 if(diag_fd>=0){
  diag_used=1;diag_live=!ready(diag_fd,now());int f[]={diag_fd},d[]={0},a[]={0},c[]={0};
  diag_reaped=stop_set(f,1,d,a,c)&&d[0];
  diag_eof=eof_until(out[0],65536)&&eof_until(err[0],4096);
 }
 if(memcmp(&frozen,&result,sizeof(result)))return 5;
finish:
 no_children=harness_no_children();
 {
  int list[]={gate[0],gate[1],out[0],out[1],err[0],err[1],event[0],event[1],r.pidfd,h.pidfd,diag_fd,original_erased};
  for(unsigned i=0;i<sizeof(list)/sizeof(*list);i++)if(list[i]>=0)close(list[i]);
 }
 int64_t ended=now();int in_budget=ended<deadline;
 printf("{\"status\":\"%s\",\"availability\":\"%s\",\"kernel_error\":\"%s\",\"case_exercised\":%s,\"kernel_copyout_observed\":%s,\"pid_return_used_for_target\":false,\"pid_return_discarded\":%s,\"candidate_helper_signal_calls\":%d,\"sigchld_verified\":%s,\"signal_seen\":%s,\"create_calls\":%d,\"slot_repeat_denied\":%s,\"r_reaped\":%s,\"candidate\":{\"binding_known\":%s,\"helper_reaped\":%s,\"wnowait_repeatable\":%s,\"wait_consumed\":%s,\"stdout_eof\":%s,\"stderr_eof\":%s,\"cleanup_confirmed\":%s,\"unknown_creation\":%s,\"production_feasible\":false,\"profile_selected\":false,\"capture_allowed\":false,\"authorizes_actions\":false,\"dev_observed\":false,\"goal_verified\":false},\"diagnostic\":{\"used\":%s,\"h_live_before\":%s,\"exact_reap\":%s,\"both_eof\":%s},\"no_children\":%s,\"within_original_deadline\":%s,\"elapsed_ms\":%llu,\"full_atomicity_proven\":false}\n",
 status,availability,kernel_error,json_bool(case_ran),json_bool(kernel_copyout),json_bool(h.discarded),helper_signals,json_bool(sig_ok),json_bool(noticed),attempts,json_bool(slot_repeat_denied),json_bool(r_reaped),json_bool(result.known),json_bool(result.reaped),json_bool(result.wnowait),json_bool(result.consumed),json_bool(result.stdout_eof==1),json_bool(result.stderr_eof==1),json_bool(result.confirmed),json_bool(result.unknown),json_bool(diag_used),json_bool(diag_live),json_bool(diag_reaped),json_bool(diag_eof),json_bool(no_children),json_bool(in_budget),(unsigned long long)((ended-ta)/1000000));
 return no_children&&in_budget?0:6;
}
