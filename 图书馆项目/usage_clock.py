"""Durable accumulated application runtime; never count offline time."""
import json,time,threading
from pathlib import Path
from catalog import atomic_json

class UsageClock:
    def __init__(self,root,clock=time.monotonic):
        self.root=Path(root);self.clock=clock;self.lock=threading.RLock();self.closed=False
        self.path=self.root/'usage.json';self.recovery=self.root/'usage-recovery.json'
        totals=[]
        for path in (self.path,self.recovery):
            if path.exists():
                value=json.loads(path.read_text('utf-8'))['total_seconds']
                if not isinstance(value,(int,float)) or value<0:raise ValueError('使用时长记录无效')
                totals.append(value)
        self.base=max(totals,default=0);self.started=clock();self.last_save=self.started
        self.stop=threading.Event();self.error=None;self.save(True)
        self.thread=threading.Thread(target=self._run,daemon=True);self.thread.start()
    def seconds(self):
        return self.base+max(0,self.clock()-self.started)
    def save(self,full=False):
        with self.lock:
            seconds=self.seconds();minutes=int(seconds//60)
            record={'total_seconds':seconds,'D':minutes//1440,'H':minutes//60%24,'M':minutes%60}
            atomic_json(self.recovery,record)
            if full:atomic_json(self.path,record);self.last_save=self.clock()
    def _run(self):
        while not self.stop.wait(10):
            try:self.save(self.clock()-self.last_save>=300);self.error=None
            except Exception as ex:self.error=str(ex)
    def close(self):
        if self.closed:return
        self.stop.set();self.thread.join();self.save(True);self.closed=True
