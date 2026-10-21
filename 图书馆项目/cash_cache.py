"""Disk cache. Most recently used entries appear first in index.json."""
import hashlib, time, base64, re
from pathlib import Path
from catalog import atomic_json
import json

class CashCache:
    def __init__(self,root,maximum=3000,retain=1500):
        self.root=Path(root);self.root.mkdir(parents=True,exist_ok=True);self.maximum=maximum;self.retain=retain
        self.index=self.root/'index.json';self.entries={};self.dirty=False
        if self.index.exists():
            data=json.loads(self.index.read_text(encoding='utf-8-sig'))
            self.entries={e['key']:e for e in data.get('entries',[]) if re.fullmatch(r'[a-f0-9]{64}',e.get('key','')) and (self.root/(e['key']+'.jpg')).is_file()}
        self.prune();self.flush()
    def key(self,p,variant=""):
        p=Path(p);st=p.stat()
        return hashlib.sha256(f'{p.resolve()}|{st.st_size}|{st.st_mtime_ns}{variant}'.encode()).hexdigest()
    def touch(self,key):
        if key in self.entries:self.entries[key]['last_used']=time.time_ns();self.dirty=True
    def get(self,p,variant=""):
        key=self.key(p,variant)
        if key in self.entries:
            try:
                image=(self.root/(key+'.jpg')).read_bytes();self.touch(key)
                return key,'data:image/jpeg;base64,'+base64.b64encode(image).decode()
            except OSError:self.entries.pop(key);self.dirty=True
        return key,None
    def add(self,key,p):
        st=Path(p).stat();self.entries[key]={'key':key,'pdf':str(p),'file':key+'.jpg','size':st.st_size,'mtime_ns':st.st_mtime_ns,'last_used':time.time_ns()};self.dirty=True;self.prune()
    def prune(self):
        if len(self.entries)>self.maximum:
            old=sorted(self.entries,key=lambda key:self.entries[key]['last_used'],reverse=True)[self.retain:]
            for key in old:
                (self.root/(key+'.jpg')).unlink(missing_ok=True);self.entries.pop(key)
            self.dirty=True
    def flush(self):
        if self.dirty or not self.index.exists():
            atomic_json(self.index,{'version':1,'policy':'LRU','maximum':self.maximum,'retain_after_cleanup':self.retain,'entries':sorted(self.entries.values(),key=lambda e:e['last_used'],reverse=True)})
            self.dirty=False
