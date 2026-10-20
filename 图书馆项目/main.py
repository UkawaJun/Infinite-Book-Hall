import json, os, sys, hashlib, math, multiprocessing, subprocess
from pathlib import Path
from datetime import datetime
from concurrent.futures import ProcessPoolExecutor
from PyQt6.QtCore import QObject, pyqtSlot, pyqtSignal, QUrl, QTimer
from PyQt6.QtWidgets import QApplication, QMainWindow, QFileDialog, QMessageBox
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEngineSettings
from music_library import handle as music_handle
from PyQt6.QtWebChannel import QWebChannel
from catalog import Catalog, identity, atomic_json, BOOK_EXTENSIONS
from layout import plan
from cover_worker import render_cover
from cash_cache import CashCache
BASE=Path(sys.executable if getattr(sys,'frozen',False) else __file__).resolve().parent
ASSETS=Path(getattr(sys,'_MEIPASS',BASE))/'web'
DATA=Path(os.environ.get('LOCALAPPDATA',str(Path.home())))/'VirtualLibrary'

class Bridge(QObject):
    coverReady=pyqtSignal(str)
    workerDone=pyqtSignal(object)
    def __init__(self,window):
        super().__init__();self.window=window;DATA.mkdir(parents=True,exist_ok=True)
        self.db=Catalog(DATA/'library.sqlite3');self.file=BASE/'personal.json';self.entries={};self.books={};self.stack=[];self.current=None
        self.positions={};self.maze=None;self.roomkey=None;self.pool=None;self.pending={}
        self.cash=CashCache(BASE/'CASH');self.workerDone.connect(self.finish_cover)
        self.cache_timer=QTimer(self);self.cache_timer.setSingleShot(True);self.cache_timer.timeout.connect(self.cash.flush)
        (BASE/'music').mkdir(exist_ok=True)
        self.cfg=json.loads(self.file.read_text(encoding='utf-8-sig')) if self.file.exists() else {'entrances':[]}
        if not self.file.exists():self.save()
    def normalize_entrances(self):
        entries=self.cfg.get('entrances',[]);unique={}
        for entry in entries:
            unique.setdefault(self.path(entry),entry)
        roots=[p for p in unique if not any(parent!=p and parent in p.parents for parent in unique)]
        overrides=self.cfg.setdefault('room_overrides',{})
        for p,e in unique.items():
            if p not in roots:overrides[str(p)]=e
        self.cfg['entrances']=[unique[p] for p in roots]
    def close(self):
        self.cash.flush()
        if self.pool:self.pool.shutdown(wait=False,cancel_futures=True)
    def save(self):atomic_json(self.file,self.cfg)
    def path(self,e):
        p=Path(os.path.expandvars(e['path'])).expanduser()
        return p.resolve() if p.is_absolute() else (self.file.parent/p).resolve()
    def bookdata(self,p,bid,b):
        st=p.stat();self.books[bid]=p;digest=hashlib.sha256(p.name.encode()).digest()
        color='#'+''.join(f'{70+v%140:02x}' for v in digest[:3])
        return {'id':bid,'name':p.name,'path':str(p),'slot':b['order'],'order':b['order'],'pages':b.get('pages'),'pages_estimated':b.get('pages_estimated',p.suffix.lower()=='.epub'),'width':b['width'],'shelf':b['shelf'],'row':b['row'],'color':color,'date':datetime.fromtimestamp(st.st_mtime).strftime('%Y-%m-%d %H:%M'),'size':round(st.st_size/1048576,2),'x':b.get('x'),'y':b.get('y')}
    def state(self):
        e=self.current;p=self.path(e) if e else None
        title=e.get('name',p.name) if e else '无限回廊 · 大厅'
        common={'title':title,'destination':str(p) if p else None}
        if p and (e.get('type') in ('furniture','shelves') or not any(d.is_dir() for d in p.iterdir())):
            data=self.db.sync(p);books=[self.bookdata(p/b['name'],bid,b) for bid,b in data['books'].items()];notes=[]
            if e.get('type')=='furniture':
                for f in sorted(p.iterdir()):
                    if f.is_file() and f.suffix.lower()=='.txt':
                        with f.open(encoding='utf-8-sig',errors='replace') as stream:text=stream.read(60)
                        notes.append({'name':f.name,'text':text})
            return dict(common,mode='furniture' if e.get('type')=='furniture' else 'shelves',books=books,notes=notes,shelf_count=data['shelf_count'],row_width=data['row_width'],book_gap=data['book_gap'])
        entries=self.cfg['entrances'] if p is None else [{'name':d.name,'path':str(d)} for d in sorted(p.iterdir()) if d.is_dir() and d.name!='.library-cache']
        if p and any(f.is_file() and f.suffix.lower() in BOOK_EXTENSIONS for f in p.iterdir()):entries.insert(0,{'name':'本层书架','path':str(p),'type':'shelves'})
        if p:entries=[dict(item,**{k:v for k,v in self.cfg.get('room_overrides',{}).get(str(self.path(item)),{}).items() if k in ('name','type')}) if item.get('type')!='shelves' else item for item in entries]
        rows=[];self.entries={}
        for item in entries:
            eid=identity(self.path(item))+'-'+item.get('type','room')
            if eid in self.entries:continue
            self.entries[eid]=item;rows.append({'id':eid,'name':item.get('name',self.path(item).name),'available':self.path(item).is_dir()})
        self.roomkey=identity(p) if p else 'lobby';self.maze=plan(self.cfg,self.roomkey,[r['id'] for r in rows])
        self.positions.setdefault(self.roomkey,0)
        if self.positions[self.roomkey]>=self.maze['size']**2:self.positions[self.roomkey]=0
        return dict(common,mode='maze',entries=rows,layout=self.maze,player=self.positions[self.roomkey])
    def request_covers(self,ids,batch,hd=False):
        if len(ids)>720:raise ValueError('单批最多 720 本')
        if not self.pool:self.pool=ProcessPoolExecutor(max_workers=2,mp_context=multiprocessing.get_context('spawn'))
        for bid in dict.fromkeys(ids):
            try:
                p=self.books[bid];key,image=self.cash.get(p,"|hd1800" if hd else "")
                if image is not None:
                    self.coverReady.emit(json.dumps({'batch':batch,'id':bid,'cover':image}));continue
                if key in self.pending:
                    self.pending[key]['listeners'].append((bid,batch));continue
                future=self.pool.submit(render_cover,str(p),str(self.cash.root/(key+'.jpg')),1800 if hd else 450)
                self.pending[key]={'future':future,'path':p,'listeners':[(bid,batch)]}
                def done(f,key=key):
                    try:result=f.result()
                    except Exception:result=''
                    try:self.workerDone.emit((key,result))
                    except RuntimeError:pass
                future.add_done_callback(done)
            except Exception:self.coverReady.emit(json.dumps({'batch':batch,'id':bid,'cover':''}))
        self.cash.flush()
    @pyqtSlot(object)
    def finish_cover(self,result):
        key,image=result;pending=self.pending.pop(key,None)
        if not pending:return
        if image:
            try:self.cash.add(key,pending['path']);self.cache_timer.start(300)
            except Exception:pass
        for bid,batch in pending['listeners']:
            self.coverReady.emit(json.dumps({'batch':batch,'id':bid,'cover':image}))
    @pyqtSlot(str,str,result=str)
    def call(self,action,payload):
        try:
            data=json.loads(payload)
            if action.startswith('music_'):
                return json.dumps(music_handle(self,action,data),ensure_ascii=False)
            if action=='ready':
                self.normalize_entrances()
                last=self.cfg.get('last_room')
                if last and self.path(last).is_dir():self.current=last
            elif action=='home':self.current=None;self.stack=[];self.positions['lobby']=0
            elif action=='back':self.current=self.stack.pop() if self.stack else None
            elif action=='walk':
                d=data['direction'];cell=self.positions.get(self.roomkey,0)
                if not isinstance(d,int) or d not in range(4):raise ValueError('无效方向')
                if not self.maze['walls'][cell][d]:self.positions[self.roomkey]=cell+[-self.maze['size'],1,self.maze['size'],-1][d]
                return json.dumps({'player':self.positions[self.roomkey]})
            elif action=='enter':
                e=self.entries[data['id']]
                if self.positions.get(self.roomkey,0)!=self.maze['placements'][data['id']]:raise ValueError('请先用方向键走到这个入口格子')
                if not self.path(e).is_dir():raise ValueError('入口正在维护中')
                self.stack.append(self.current);self.current=e
                if identity(self.path(e))!=self.roomkey:self.positions[identity(self.path(e))]=0
            elif action=='covers':self.request_covers(data['ids'],data.get('batch',''),bool(data.get('hd')));return '{}'
            elif action=='settings':return json.dumps({'entrances':self.cfg['entrances']},ensure_ascii=False)
            elif action=='browse':return json.dumps({'path':QFileDialog.getExistingDirectory(self.window,'选择书室文件夹')})
            elif action=='saveSettings':
                for e in data['entrances']:
                    if not str(e.get('path','')).strip():raise ValueError('文件夹路径不能为空')
                self.cfg['entrances']=data['entrances'];self.normalize_entrances();self.save();self.current=None;self.stack=[]
            elif action=='folder':
                p=self.books[data['id']]
                if not p.is_file():raise FileNotFoundError(str(p))
                subprocess.Popen(['explorer.exe','/select,',str(p)]);return '{}'
            elif action=='reveal':
                p=self.books[data['id']]
                if not p.is_file():raise FileNotFoundError(str(p))
                subprocess.Popen(['explorer.exe','/select,',str(p)])
                os.startfile(str(p));return '{}'

            elif action=='rename':
                old=data['id'];target=self.db.rename(self.books[old],data['name']);new=identity(target)
                self.books[new]=target
                if new!=old:self.books.pop(old,None)
                record=self.db.sync(target.parent)['books'][new]
                return json.dumps({'old_id':old,'new_id':new,'book':self.bookdata(target,new,record),'state':self.state()},ensure_ascii=False)
            elif action=='move':
                x,y=float(data['x']),float(data['y'])
                if not math.isfinite(x) or not math.isfinite(y):raise ValueError('无效坐标')
                self.db.move(self.books[data['id']],max(0,x),max(0,y));return '{}'
            elif action=='reorder':self.db.reorder(self.books[data['id']],data['shelf'],data['row'],data.get('before'));return json.dumps(self.state(),ensure_ascii=False)
            elif action=='putdown':
                if not self.current:raise ValueError('请先走进要放书的目标房间')
                dest=self.path(self.current);moved=[];errors=[]
                for bid in dict.fromkeys(data['ids']):
                    try:
                        p=self.books[bid];target=self.db.transfer(p,dest);self.books[identity(target)]=target;moved.append(bid)
                    except Exception as ex:errors.append({'id':bid,'message':str(ex)})
                return json.dumps({'moved':moved,'errors':errors,'state':self.state()},ensure_ascii=False)
            self.cfg['last_room']=self.current;result=self.state();self.save();return json.dumps(result,ensure_ascii=False)
        except Exception as ex:return json.dumps({'error':str(ex)},ensure_ascii=False)

class Window(QMainWindow):
    def __init__(self):
        super().__init__();self.setWindowTitle('无限图书回廊');self.resize(1380,920)
        self.web=QWebEngineView();self.setCentralWidget(self.web);self.bridge=Bridge(self)
        self.channel=QWebChannel();self.channel.registerObject('library',self.bridge);self.web.page().setWebChannel(self.channel)
        self.web.settings().setAttribute(QWebEngineSettings.WebAttribute.PlaybackRequiresUserGesture,False)
        self.web.setUrl(QUrl.fromLocalFile(str(ASSETS/'index.html')))
        if '--smoke-test' in sys.argv:
            self.web.loadFinished.connect(self.smoke);QTimer.singleShot(45000,lambda:QApplication.exit(3))
    def closeEvent(self,event):self.bridge.close();super().closeEvent(event)
    def smoke(self,ok):
        if not ok:QApplication.exit(2);return
        QTimer.singleShot(2500,self.verify)
    def verify(self):
        self.grab().save(str(BASE/'preview-pyqt.png'))
        self.web.page().runJavaScript((ASSETS/'smoke.js').read_text(encoding='utf-8'))
        self.poll_smoke()
    def capture_phase(self,phase):
        if phase in ('overview','shelf') and getattr(self,'last_capture',None)!=phase:
            self.last_capture=phase;self.grab().save(str(BASE/f'preview-{phase}.png'))
    def poll_smoke(self):
        self.web.page().runJavaScript('document.body.dataset.capture || ""',self.capture_phase)
        self.web.page().runJavaScript('document.body.dataset.test || ""',self.smoke_result)
    def smoke_result(self,result):
        if not result:QTimer.singleShot(500,self.poll_smoke)
        else:
            (BASE/'smoke-result.txt').write_text(result,encoding='utf-8');self.bridge.close();QApplication.exit(0 if result=='ok' else 4)

if __name__=='__main__':
    multiprocessing.freeze_support()
    app=QApplication(sys.argv)
    try:window=Window();window.show();sys.exit(app.exec())
    except Exception as ex:
        import traceback
        (BASE/'startup-error.log').write_text(traceback.format_exc(),encoding='utf-8')
        QMessageBox.critical(None,'启动失败',str(ex));sys.exit(1)
