#define _GNU_SOURCE
#include "sqlite_abi.h"
#include "native_schema.h"
#include <sys/stat.h>
#include <sys/random.h>
#include <unistd.h>
#include <fcntl.h>
#include <signal.h>
#include <errno.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>
#include <stdint.h>

/* No OpenCode/ContextRegistry constructor, no source writable fd, no subprocess.
 * POSIX locks are delegated to the same native unix VFS used by writers.
 * Keep every fd for this inode open until SQLite has unlocked and closed. */
typedef struct { sqlite3_file file; sqlite3_file *base; } RFile;
static sqlite3_vfs *unix_vfs;
static int dbfd,dirfd_,violated,opened,role;
static char alias[80];
static const char *basename_;
static struct stat original;
static unsigned char response[65536];
static size_t used;
static int open_rc,base_rc,base_errno,open_flags;
#ifdef OC_CONTROL_BUILD
static int stage;
static int probe_mode,releasefd=-1,auth_rc;
#define STAGE(n) (stage=(n))
#else
#define STAGE(n) ((void)0)
#endif

static int deny(void) { violated=1; return SQLITE_IOERR; }
static void expired(int sig) { (void)sig; _exit(72); }
static int same(const struct stat *s) {
 return S_ISREG(s->st_mode) && s->st_dev==original.st_dev &&
  s->st_ino==original.st_ino && s->st_uid==geteuid() && s->st_nlink==1 &&
  (s->st_mode&07777)==0600 && s->st_size>0 && s->st_size<=67108864;
}
static int binding(void) {
 struct stat f,e,d;
 return fstat(dbfd,&f)==0 && same(&f) &&
  fstatat(dirfd_,basename_,&e,AT_SYMLINK_NOFOLLOW)==0 && same(&e) &&
  fstat(dirfd_,&d)==0 && S_ISDIR(d.st_mode) && d.st_uid==geteuid() &&
  (d.st_mode&07777)==0700;
}
/* The default unix VFS opens O_NOFOLLOW. Do not resolve the proc-fd symlink
 * to a mutable pathname. In this dedicated single-connection process only,
 * its documented named syscall interface maps this ONE alias to dup(capfd).
 * All byte reads and POSIX lock operations still use the standard unix VFS.
 * There is no saved native-open fallback and no caller-settable syscall. */
static int cap_open(const char *name,int flags,mode_t mode) {
 (void)mode;
 const int allowed=O_RDONLY|O_NOFOLLOW|O_CLOEXEC|O_LARGEFILE;
 if(!name || strcmp(name,alias) || (flags&~allowed) || !binding()) {
  violated=1;errno=EACCES;return -1;
 }
 return fcntl(dbfd,F_DUPFD_CLOEXEC,3);
}
static int no_sidecars(void) {
 const char *suffix[]={"-journal","-wal","-shm"};
 char name[128]; struct stat s;
 for (int i=0;i<3;i++) {
  if (snprintf(name,sizeof(name),"%s%s",basename_,suffix[i])>=(int)sizeof(name)) return 0;
  if (fstatat(dirfd_,name,&s,AT_SYMLINK_NOFOLLOW)==0 || errno!=ENOENT) return 0;
 }
 return 1;
}
#define RF(f) ((RFile*)(f))
#define M(f) (RF(f)->base->pMethods)
static int rClose(sqlite3_file *f) { return M(f)->xClose(RF(f)->base); }
static int rRead(sqlite3_file *f,void *p,int n,sqlite3_int64 o) {
 if(n<0 || o<0 || o>67108864 || n>67108864-o) return deny();
 return M(f)->xRead(RF(f)->base,p,n,o);
}
static int rWrite(sqlite3_file *f,const void*p,int n,sqlite3_int64 o) { (void)f;(void)p;(void)n;(void)o;return deny(); }
static int rTruncate(sqlite3_file*f,sqlite3_int64 n) { (void)f;(void)n;return deny(); }
static int rSync(sqlite3_file*f,int n) { (void)f;(void)n;return deny(); }
static int rSize(sqlite3_file*f,sqlite3_int64*n) { return M(f)->xFileSize(RF(f)->base,n); }
static int rLock(sqlite3_file*f,int n) {
 if(n!=SQLITE_LOCK_SHARED) return deny();
 return M(f)->xLock(RF(f)->base,n);
}
static int rUnlock(sqlite3_file*f,int n) {
 if(n!=SQLITE_LOCK_NONE && n!=SQLITE_LOCK_SHARED) return deny();
 return M(f)->xUnlock(RF(f)->base,n);
}
static int rReserved(sqlite3_file*f,int*n) { return M(f)->xCheckReservedLock(RF(f)->base,n); }
static int rControl(sqlite3_file*f,int op,void *p) {
 /* LOCKSTATE=1, LAST_ERRNO=4, HAS_MOVED=20 are safe native queries.
  * All unrecognized controls get NOTFOUND, never delegated blindly. */
 if(op==1 || op==4 || op==20) return M(f)->xFileControl(RF(f)->base,op,p);
 return SQLITE_NOTFOUND;
}
static int rSector(sqlite3_file*f) { return M(f)->xSectorSize(RF(f)->base); }
static int rDevice(sqlite3_file*f) { (void)f;return 0; }
static int rShmMap(sqlite3_file*f,int a,int b,int c,void volatile**p) { (void)f;(void)a;(void)b;(void)c;(void)p;return deny(); }
static int rShmLock(sqlite3_file*f,int a,int b,int c) { (void)f;(void)a;(void)b;(void)c;return deny(); }
static void rShmBarrier(sqlite3_file*f) { (void)f;violated=1; }
static int rShmUnmap(sqlite3_file*f,int a) { (void)f;(void)a;return deny(); }
static int rFetch(sqlite3_file*f,sqlite3_int64 a,int b,void**p) { (void)f;(void)a;(void)b;*p=NULL;return SQLITE_OK; }
static int rUnfetch(sqlite3_file*f,sqlite3_int64 a,void*p) { (void)f;(void)a;(void)p;return SQLITE_OK; }
static const sqlite3_io_methods methods={3,rClose,rRead,rWrite,rTruncate,rSync,rSize,rLock,rUnlock,rReserved,rControl,rSector,rDevice,rShmMap,rShmLock,rShmBarrier,rShmUnmap,rFetch,rUnfetch};
static int vOpen(sqlite3_vfs*v,const char *name,sqlite3_file *f,int flags,int*out) {
 (void)v; RFile*r=RF(f); r->file.pMethods=NULL;
 open_flags=flags;
 if(!name || strcmp(name,alias) || opened || flags!=(SQLITE_OPEN_READONLY|SQLITE_OPEN_MAIN_DB) || !binding()) return deny();
 r->base=(sqlite3_file*)(r+1); memset(r->base,0,(size_t)unix_vfs->szOsFile);
 int rc=unix_vfs->xOpen(unix_vfs,name,r->base,flags,out);
 base_rc=rc;base_errno=errno;
 if(rc!=SQLITE_OK) { if(r->base->pMethods) r->base->pMethods->xClose(r->base); return rc; }
 if(!r->base->pMethods || r->base->pMethods->iVersion<1 || !binding()) {
  if(r->base->pMethods) r->base->pMethods->xClose(r->base);
  return deny();
 }
 opened=1;r->file.pMethods=&methods;return SQLITE_OK;
}
static int vDelete(sqlite3_vfs*v,const char*n,int s) { (void)v;(void)n;(void)s;return deny(); }
static int vAccess(sqlite3_vfs*v,const char*n,int flags,int*out) {
 (void)v;(void)flags;
 if(n && !strcmp(n,alias)) { *out=binding();return *out?SQLITE_OK:deny(); }
 const char*suf[]={"-journal","-wal","-shm"};char x[128];
 for(int i=0;i<3;i++) {
  snprintf(x,sizeof(x),"%s%s",alias,suf[i]);
  if(n && !strcmp(n,x)) { if(!no_sidecars()) return deny();*out=0;return SQLITE_OK; }
 }
 return deny();
}
static int vFull(sqlite3_vfs*v,const char*n,int cap,char*out) {
 (void)v;
 if(!n || strcmp(n,"oc-bound-main") || cap<=(int)strlen(alias)) return deny();
 memcpy(out,alias,strlen(alias)+1);return SQLITE_OK;
}
static void *vDlOpen(sqlite3_vfs*v,const char*n) { (void)v;(void)n;violated=1;return NULL; }
static void vDlError(sqlite3_vfs*v,int n,char*p) { (void)v;if(n>0)*p=0; }
static void (*vDlSym(sqlite3_vfs*v,void*p,const char*n))(void) { (void)v;(void)p;(void)n;violated=1;return NULL; }
static void vDlClose(sqlite3_vfs*v,void*p) { (void)v;(void)p;violated=1; }
static int vRandom(sqlite3_vfs*v,int n,char*p) {
 (void)v;if(n<0||n>65536){violated=1;return 0;}
 ssize_t got=getrandom(p,(size_t)n,0);if(got<0){violated=1;return 0;}return (int)got;
}
static int vSleep(sqlite3_vfs*v,int n) { (void)v;(void)n;violated=1;return 0; }
static int vTime(sqlite3_vfs*v,double*p) { (void)v;return unix_vfs->xCurrentTime(unix_vfs,p); }
static int vError(sqlite3_vfs*v,int n,char*p) { (void)v;if(n>0)*p=0;return 0; }
static int vTime64(sqlite3_vfs*v,sqlite3_int64*p) { (void)v;return unix_vfs->xCurrentTimeInt64(unix_vfs,p); }

static const char *jobcols[]={"job_id","request_id","session_id","model","workspace","binary","fingerprint","status","exit_code","log_path","max_output_bytes","transition_actor","transition_reason","cancel_flag"};
static int authorize(void*p,int op,const char*a,const char*b,const char*c,const char*d) {
 (void)p;(void)c;(void)d;
 if(op==SQLITE_SELECT) return SQLITE_OK;
 if(op==SQLITE_TRANSACTION && a && (!strcmp(a,"BEGIN") || !strcmp(a,"COMMIT") || !strcmp(a,"ROLLBACK"))) return SQLITE_OK;
 if(op==SQLITE_READ && a && b) {
  if(!strcmp(a,"sqlite_master") || !strcmp(a,"sqlite_schema")) {
   if(!strcmp(b,"type")||!strcmp(b,"name")||!strcmp(b,"tbl_name")||!strcmp(b,"sql")) return SQLITE_OK;
  }
  if(role==1 && !strcmp(a,"jobs")) for(unsigned i=0;i<sizeof(jobcols)/sizeof(*jobcols);i++) if(!strcmp(b,jobcols[i])) return SQLITE_OK;
  if(role==2 && !strcmp(a,"contexts") && (!strcmp(b,"context_id")||!strcmp(b,"closed"))) return SQLITE_OK;
 }
 violated=1;return SQLITE_DENY;
}
static int normalized(const char*s,const char*expected) {
 char buf[8192];size_t n=0;int space=0;
 if(!s) return 0;
 for(;*s;s++) {
  if(isspace((unsigned char)*s)) { space=n>0;continue; }
  if(space) { if(n>=sizeof(buf)-1)return 0;buf[n++]=' ';space=0; }
  if(n>=sizeof(buf)-1)return 0;
  buf[n++]=*s;
 }
 buf[n]=0;return !strcmp(buf,expected);
}
static int schema(sqlite3*db) {
 sqlite3_stmt*s=NULL;int ok=1,count=0,tables=0;
 if(sqlite3_prepare_v2(db,"SELECT type,name,tbl_name,sql FROM sqlite_schema ORDER BY type,name",-1,&s,NULL)!=SQLITE_OK) return 0;
 int rc;
 while((rc=sqlite3_step(s))==SQLITE_ROW) {
  const char *type=(const char*)sqlite3_column_text(s,0),*name=(const char*)sqlite3_column_text(s,1),*table=(const char*)sqlite3_column_text(s,2),*sql=(const char*)sqlite3_column_text(s,3);
  count++;
  const char*want=role==1?"jobs":"contexts";
  if(!type||!name||!table||strcmp(table,want)) {ok=0;break;}
  if(!strcmp(type,"table") && !strcmp(name,want) && normalized(sql,role==1?schema_jobs:schema_contexts)) tables++;
  else if(!strcmp(type,"index") && !sql &&
    (role==1?(!strcmp(name,"sqlite_autoindex_jobs_1")||!strcmp(name,"sqlite_autoindex_jobs_2")):!strcmp(name,"sqlite_autoindex_contexts_1"))) { }
  else {ok=0;break;}
  if(count>3){ok=0;break;}
 }
 if(rc!=SQLITE_DONE)ok=0;
 if(sqlite3_finalize(s)!=SQLITE_OK)ok=0;
 return ok && tables==1 && count==(role==1?3:2);
}
static int append(const void*p,size_t n) {if(n>sizeof(response)-used)return 0;memcpy(response+used,p,n);used+=n;return 1;}
static int field(sqlite3_stmt*s,int i) {
 int type=sqlite3_column_type(s,i);unsigned char tag=(unsigned char)type;unsigned char bytes[8];
 if(!append(&tag,1))return 0;
 if(type==SQLITE_NULL)return 1;
 if(type==SQLITE_INTEGER || type==SQLITE_FLOAT) {
  uint64_t v;
  if(type==SQLITE_INTEGER)v=(uint64_t)sqlite3_column_int64(s,i);
  else {double d=sqlite3_column_double(s,i);memcpy(&v,&d,8);}
  for(int k=0;k<8;k++)bytes[k]=(unsigned char)(v>>(56-8*k));
  return append(bytes,8);
 }
 if(type==SQLITE_TEXT) {
  int n=sqlite3_column_bytes(s,i);const void*p=sqlite3_column_text(s,i);
  if(n<0||n>8192||!p)return 0;
  uint32_t x=(uint32_t)n;for(int k=0;k<4;k++)bytes[k]=(unsigned char)(x>>(24-8*k));
  return append(bytes,4)&&append(p,(size_t)n);
 }
 return 0;
}
static int query(sqlite3*db,const char*id) {
 const char*q=role==1?"SELECT job_id,request_id,session_id,model,workspace,binary,fingerprint,status,exit_code,log_path,max_output_bytes,transition_actor,transition_reason,cancel_flag FROM jobs WHERE job_id=?":"SELECT context_id,closed FROM contexts WHERE context_id=?";
 sqlite3_stmt*s=NULL;int ok=0;
 if(sqlite3_prepare_v2(db,q,-1,&s,NULL)!=SQLITE_OK)return 0;
 if(sqlite3_bind_text(s,1,id,-1,NULL)!=SQLITE_OK)goto done;
 if(sqlite3_step(s)!=SQLITE_ROW)goto done;
 int n=sqlite3_column_count(s);unsigned char prefix[2]={(unsigned char)role,(unsigned char)n};
 if(!append("OCSNAP1\0",8)||!append(prefix,2))goto done;
 for(int i=0;i<n;i++)if(!field(s,i))goto done;
 ok=sqlite3_step(s)==SQLITE_DONE;
 done: if(sqlite3_finalize(s)!=SQLITE_OK)ok=0;return ok;
}
static int fdarg(const char*s) {char*end;long x=strtol(s,&end,10);return *s&&!*end&&x>2&&x<1048576?(int)x:-1;}
static int target(char*s,size_t cap) {
 if(!fgets(s,(int)cap,stdin))return 0;
 size_t n=strlen(s);if(n<2||s[n-1]!='\n')return 0;s[--n]=0;
 if(n>128)return 0;
 for(size_t i=0;i<n;i++)if(!isalnum((unsigned char)s[i])&&s[i]!='_'&&s[i]!='-'&&s[i]!='.')return 0;
 return 1;
}
static int capture_one(int sourcefd,int directoryfd,const char*r,const char*id) {
 sqlite3*db=NULL;int good=0;
 dbfd=sourcefd;dirfd_=directoryfd;used=0;opened=0;
 if(violated)return 2;
 role=!strcmp(r,"jobs")?1:!strcmp(r,"context")?2:0;
 STAGE(1);
 if(!role)goto end;
 basename_=role==1?"opencode-tasks.sqlite3":"contexts.sqlite3";
 if(fstat(dbfd,&original)||!binding()||
#ifdef OC_CONTROL_BUILD
    (!probe_mode&&!no_sidecars())||
#else
    !no_sidecars()||
#endif
    (fcntl(dbfd,F_GETFL)&O_ACCMODE)!=O_RDONLY||sqlite3_libversion_number()!=3045001)goto end;
 unsigned char hdr[100];
 STAGE(2);
 if(pread(dbfd,hdr,sizeof(hdr),0)!=(ssize_t)sizeof(hdr)||memcmp(hdr,"SQLite format 3\0",16)||hdr[18]!=1||hdr[19]!=1)goto end;
 unix_vfs=sqlite3_vfs_find("unix");
 STAGE(3);
 if(!unix_vfs||unix_vfs->iVersion<3||!unix_vfs->xSetSystemCall||!unix_vfs->xGetSystemCall||
    !unix_vfs->xGetSystemCall(unix_vfs,"open")||unix_vfs->szOsFile<=0||unix_vfs->szOsFile>65536)goto end;
 snprintf(alias,sizeof(alias),"/proc/self/fd/%d",dbfd);
 if(unix_vfs->xSetSystemCall(unix_vfs,"open",(void(*)(void))cap_open)!=SQLITE_OK)goto end;
 static sqlite3_vfs v;memset(&v,0,sizeof(v));v.iVersion=2;v.szOsFile=(int)sizeof(RFile)+unix_vfs->szOsFile;v.mxPathname=4096;v.zName="oc-retained-readonly";
 v.xOpen=vOpen;v.xDelete=vDelete;v.xAccess=vAccess;v.xFullPathname=vFull;
 v.xDlOpen=vDlOpen;v.xDlError=vDlError;v.xDlSym=vDlSym;v.xDlClose=vDlClose;
 v.xRandomness=vRandom;v.xSleep=vSleep;v.xCurrentTime=vTime;v.xGetLastError=vError;v.xCurrentTimeInt64=vTime64;
 struct sigaction action={0};action.sa_handler=expired;sigemptyset(&action.sa_mask);
 if(sigaction(SIGALRM,&action,NULL))goto end;
 alarm(1); /* Covers every native database open/lock/query/close, not just step(). */
 if(sqlite3_vfs_register(&v,0)!=SQLITE_OK)goto end;
#ifdef OC_CONTROL_BUILD
 if(probe_mode) {
  sqlite3_file*f=calloc(1,(size_t)v.szOsFile);int out=0;void*p=NULL;unsigned mask=0;
  if(!f || vOpen(&v,alias,f,257,&out)!=SQLITE_OK){free(f);goto end;}
  if(rWrite(f,"x",1,0)==SQLITE_IOERR)mask|=1;
  if(rTruncate(f,0)==SQLITE_IOERR)mask|=2;
  if(rSync(f,0)==SQLITE_IOERR)mask|=4;
  if(vDelete(&v,alias,0)==SQLITE_IOERR)mask|=8;
  if(rLock(f,2)==SQLITE_IOERR)mask|=16;
  if(rShmMap(f,0,4096,1,(void volatile**)&p)==SQLITE_IOERR)mask|=32;
  if(rShmLock(f,0,1,1)==SQLITE_IOERR)mask|=64;
  if(rControl(f,999,&out)==SQLITE_NOTFOUND)mask|=128;
  if(cap_open(alias,O_RDWR,0)<0)mask|=256;
  if(cap_open("NOT_THE_CAPABILITY",O_RDONLY,0)<0)mask|=512;
  char side[128];snprintf(side,sizeof(side),"%s-journal",alias);
  if(vAccess(&v,side,0,&out)==SQLITE_IOERR)mask|=1024;
  int closed=rClose(f);free(f);
  if(mask==2047 && closed==SQLITE_OK) {used=0;good=append("CONTROL_DENIALS=2047\n",21);}
  goto end;
 }
#endif
 STAGE(4);
 open_rc=sqlite3_open_v2("oc-bound-main",&db,SQLITE_OPEN_READONLY|SQLITE_OPEN_PRIVATECACHE,v.zName);
 if(open_rc!=SQLITE_OK)goto end;
 if(sqlite3_db_readonly(db,"main")!=1 || sqlite3_busy_timeout(db,0)!=SQLITE_OK ||
    sqlite3_db_config(db,SQLITE_DBCONFIG_DEFENSIVE,1,(int*)0)!=SQLITE_OK ||
    sqlite3_db_config(db,SQLITE_DBCONFIG_TRUSTED_SCHEMA,0,(int*)0)!=SQLITE_OK)goto end;
 STAGE(5);
 sqlite3_limit(db,0,65536);sqlite3_limit(db,1,8192);sqlite3_limit(db,2,32);sqlite3_limit(db,3,16);
 if(sqlite3_set_authorizer(db,authorize,NULL)!=SQLITE_OK)goto end;
 if(sqlite3_exec(db,"BEGIN",NULL,NULL,NULL)!=SQLITE_OK)goto end;
 STAGE(6);
 if(!schema(db))goto end;
 STAGE(7);
#ifdef OC_CONTROL_AUTHORIZE
 {sqlite3_stmt *bad=NULL;auth_rc=sqlite3_prepare_v2(db,"SELECT prompt FROM jobs",-1,&bad,NULL);
  if(bad)sqlite3_finalize(bad);
  goto end;}
#endif
 if(!query(db,id))goto end;
#ifdef OC_CONTROL_BUILD
 if(releasefd>=0) {
  if(write(STDERR_FILENO,"CONTROL_READ_LOCK\n",18)!=18)goto end;
  char byte;if(read(releasefd,&byte,1)!=1)goto end;
 }
#endif
 STAGE(8);
 if(sqlite3_exec(db,"COMMIT",NULL,NULL,NULL)!=SQLITE_OK || violated)goto end;
 STAGE(9);
 if(sqlite3_close(db)!=SQLITE_OK) {db=NULL;goto end;} db=NULL;
 if(!binding()||!no_sidecars())goto end;
 good=1;
 end:
 if(db && sqlite3_close(db)!=SQLITE_OK)good=0;
 alarm(0);
#ifdef OC_CONTROL_BUILD
 if(!good)fprintf(stderr,"CONTROL_STAGE=%d;VIOLATED=%d;OPEN=%d;BASE=%d;ERRNO=%d;FLAGS=%d;AUTH=%d\n",stage,violated,open_rc,base_rc,base_errno,open_flags,auth_rc);
#endif
 return good?0:2;
}
static int emit(int framed) {
 if(framed) {
  unsigned char n[4];for(int k=0;k<4;k++)n[k]=(unsigned char)(used>>(24-8*k));
  if(write(STDOUT_FILENO,n,4)!=4)return 2;
 }
 for(size_t pos=0;pos<used;) {
  ssize_t n=write(STDOUT_FILENO,response+pos,used-pos);if(n<=0)return 2;pos+=(size_t)n;
 }
 return 0;
}
int main(int argc,char**argv) {
 if(argc==2&&!strcmp(argv[1],"--build-facts")) {
  printf("SQLite=%s\nSource=%s\n",sqlite3_libversion(),sqlite3_sourceid());return 0;
 }
 int batch=argc==5&&!strcmp(argv[1],"--batch"), job=-1,ctx=-1,dir=-1;
#ifdef OC_CONTROL_BUILD
 if(argc==4&&!strcmp(argv[1],"--probe")) {probe_mode=1;job=fdarg(argv[2]);dir=fdarg(argv[3]);}
 else if(argc==5&&!strcmp(argv[1],"--hold-read")) {releasefd=fdarg(argv[4]);job=fdarg(argv[2]);dir=fdarg(argv[3]);batch=0;}
 else
#endif
 if(batch) {job=fdarg(argv[2]);ctx=fdarg(argv[3]);dir=fdarg(argv[4]);}
 else if(argc==3) {job=fdarg(argv[1]);dir=fdarg(argv[2]);}
 if(job<0||dir<0||job==dir||(batch&&(ctx<0||ctx==job||ctx==dir)))goto bad;
 char saved_context[132]={0};
 for(int phase=0;phase<(batch?3:1);phase++) {
  char r[16],id[132];
  if(!target(r,sizeof(r))||!target(id,sizeof(id)))goto bad;
  if(batch) {
   if(strcmp(r,phase==1?"jobs":"context"))goto bad;
   if(phase==0)memcpy(saved_context,id,strlen(id)+1);
   if(phase==2&&strcmp(id,saved_context))goto bad;
  }
  if((!batch||phase==2)&&fgetc(stdin)!=EOF)goto bad;
  int fd=batch&&phase!=1?ctx:job;
  if(capture_one(fd,dir,r,id)!=0||emit(batch)!=0)goto bad;
 }
 return 0;
 bad:
 if(write(STDOUT_FILENO,"HOLD: capture unavailable\n",26)<0)return 2;
 return 2;
}
