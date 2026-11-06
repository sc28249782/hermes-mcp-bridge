"""Load exact previously reviewed offline baseline bytes, never caller code.

The temporary canonical import alias is used only while importing store.py in
this standalone single-thread source component; it is restored immediately.
"""
import hashlib
import importlib.util
import os
from pathlib import Path
import stat
import sys

from .owner import Hold, need, read_all


def _module(name, file, expected):
    fd=os.open(file,os.O_RDONLY|os.O_NOFOLLOW)
    try:
        info=os.fstat(fd)
        need(stat.S_ISREG(info.st_mode) and info.st_uid==os.geteuid() and info.st_nlink==1 and not info.st_mode&0o022)
        raw=read_all(fd,65536)
        need(hashlib.sha256(raw).hexdigest()==expected,'BINDING_MISMATCH')
    finally:os.close(fd)
    spec=importlib.util.spec_from_loader(name,loader=None,origin=str(file))
    module=importlib.util.module_from_spec(spec)
    module.__file__=str(file)
    sys.modules[name]=module
    # Only the compiled, byte-pinned repository sources above, never input JSON.
    exec(compile(raw,str(file),'exec'),module.__dict__)
    return module


ROOT=Path(__file__).resolve().parents[1]
C=_module('_oc_handoff_checkpoint',ROOT/'checkpoint.py','b3f2b58aa939340c043f4999868b5c9989db6f7ad7b5dee74762fbd0eb4ab5ed')
old=sys.modules.get('checkpoint')
try:
    sys.modules['checkpoint']=C
    S=_module('_oc_handoff_store',ROOT/'store.py','d5106483892ea9ae4832204bdfd9c446013b44e1894e21d5f8614fe245806c97')
finally:
    if old is None:sys.modules.pop('checkpoint',None)
    else:sys.modules['checkpoint']=old
