/* Limited public SQLite 3 ABI declarations, not an alternate locking engine.
 * Layout/API references: sqlite.org/c3ref/{vfs,io_methods,open}.html.
 * This package supports the measured system SQLite 3.45.1 unix VFS only. */
#ifndef OC_SQLITE_ABI_H
#define OC_SQLITE_ABI_H
#include <stdint.h>
typedef long long sqlite3_int64;
_Static_assert(sizeof(sqlite3_int64)==8,"supported SQLite integer ABI");
_Static_assert(sizeof(void*)==8,"supported 64-bit Linux ABI");
typedef struct sqlite3 sqlite3;
typedef struct sqlite3_stmt sqlite3_stmt;
typedef struct sqlite3_file sqlite3_file;
typedef struct sqlite3_io_methods sqlite3_io_methods;
typedef struct sqlite3_vfs sqlite3_vfs;
struct sqlite3_file { const sqlite3_io_methods *pMethods; };
struct sqlite3_io_methods {
 int iVersion;
 int (*xClose)(sqlite3_file*);
 int (*xRead)(sqlite3_file*,void*,int,sqlite3_int64);
 int (*xWrite)(sqlite3_file*,const void*,int,sqlite3_int64);
 int (*xTruncate)(sqlite3_file*,sqlite3_int64);
 int (*xSync)(sqlite3_file*,int);
 int (*xFileSize)(sqlite3_file*,sqlite3_int64*);
 int (*xLock)(sqlite3_file*,int);
 int (*xUnlock)(sqlite3_file*,int);
 int (*xCheckReservedLock)(sqlite3_file*,int*);
 int (*xFileControl)(sqlite3_file*,int,void*);
 int (*xSectorSize)(sqlite3_file*);
 int (*xDeviceCharacteristics)(sqlite3_file*);
 int (*xShmMap)(sqlite3_file*,int,int,int,void volatile**);
 int (*xShmLock)(sqlite3_file*,int,int,int);
 void (*xShmBarrier)(sqlite3_file*);
 int (*xShmUnmap)(sqlite3_file*,int);
 int (*xFetch)(sqlite3_file*,sqlite3_int64,int,void**);
 int (*xUnfetch)(sqlite3_file*,sqlite3_int64,void*);
};
struct sqlite3_vfs {
 int iVersion,szOsFile,mxPathname;
 sqlite3_vfs *pNext;
 const char *zName;
 void *pAppData;
 int (*xOpen)(sqlite3_vfs*,const char*,sqlite3_file*,int,int*);
 int (*xDelete)(sqlite3_vfs*,const char*,int);
 int (*xAccess)(sqlite3_vfs*,const char*,int,int*);
 int (*xFullPathname)(sqlite3_vfs*,const char*,int,char*);
 void *(*xDlOpen)(sqlite3_vfs*,const char*);
 void (*xDlError)(sqlite3_vfs*,int,char*);
 void (*(*xDlSym)(sqlite3_vfs*,void*,const char*))(void);
 void (*xDlClose)(sqlite3_vfs*,void*);
 int (*xRandomness)(sqlite3_vfs*,int,char*);
 int (*xSleep)(sqlite3_vfs*,int);
 int (*xCurrentTime)(sqlite3_vfs*,double*);
 int (*xGetLastError)(sqlite3_vfs*,int,char*);
 int (*xCurrentTimeInt64)(sqlite3_vfs*,sqlite3_int64*);
 int (*xSetSystemCall)(sqlite3_vfs*,const char*,void(*)(void));
 void (*(*xGetSystemCall)(sqlite3_vfs*,const char*))(void);
 const char *(*xNextSystemCall)(sqlite3_vfs*,const char*);
};
extern int sqlite3_libversion_number(void);
extern const char *sqlite3_libversion(void),*sqlite3_sourceid(void);
extern sqlite3_vfs *sqlite3_vfs_find(const char*);
extern int sqlite3_vfs_register(sqlite3_vfs*,int);
extern int sqlite3_open_v2(const char*,sqlite3**,int,const char*);
extern int sqlite3_close(sqlite3*),sqlite3_db_readonly(sqlite3*,const char*);
extern int sqlite3_db_config(sqlite3*,int,...);
extern int sqlite3_limit(sqlite3*,int,int),sqlite3_busy_timeout(sqlite3*,int);
extern int sqlite3_set_authorizer(sqlite3*,int(*)(void*,int,const char*,const char*,const char*,const char*),void*);
extern int sqlite3_prepare_v2(sqlite3*,const char*,int,sqlite3_stmt**,const char**);
extern int sqlite3_step(sqlite3_stmt*),sqlite3_finalize(sqlite3_stmt*);
extern int sqlite3_bind_text(sqlite3_stmt*,int,const char*,int,void(*)(void*));
extern int sqlite3_column_count(sqlite3_stmt*),sqlite3_column_type(sqlite3_stmt*,int);
extern const unsigned char *sqlite3_column_text(sqlite3_stmt*,int);
extern int sqlite3_column_bytes(sqlite3_stmt*,int);
extern sqlite3_int64 sqlite3_column_int64(sqlite3_stmt*,int);
extern double sqlite3_column_double(sqlite3_stmt*,int);
extern int sqlite3_exec(sqlite3*,const char*,int(*)(void*,int,char**,char**),void*,char**);
#define SQLITE_OK 0
#define SQLITE_ERROR 1
#define SQLITE_BUSY 5
#define SQLITE_READONLY 8
#define SQLITE_IOERR 10
#define SQLITE_NOTFOUND 12
#define SQLITE_DENY 1
#define SQLITE_ROW 100
#define SQLITE_DONE 101
#define SQLITE_INTEGER 1
#define SQLITE_FLOAT 2
#define SQLITE_TEXT 3
#define SQLITE_NULL 5
#define SQLITE_OPEN_READONLY 0x1
#define SQLITE_OPEN_PRIVATECACHE 0x40000
#define SQLITE_OPEN_MAIN_DB 0x100
#define SQLITE_READ 20
#define SQLITE_SELECT 21
#define SQLITE_TRANSACTION 22
#define SQLITE_LOCK_NONE 0
#define SQLITE_LOCK_SHARED 1
#define SQLITE_DBCONFIG_DEFENSIVE 1010
#define SQLITE_DBCONFIG_TRUSTED_SCHEMA 1017
#endif
