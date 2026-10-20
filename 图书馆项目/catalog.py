"""Per-room JSON catalog. File paths identify books; filenames allow portable rooms."""
import hashlib, json, os, sqlite3, tempfile, shutil
from pathlib import Path
from contextlib import closing

BOOK_EXTENSIONS={'.pdf','.epub'}
CAPACITY=90
BOOK_GAP=.04
ROW_WIDTH=15+14*BOOK_GAP
MAX_WIDTH=1.25

def identity(path):
    return hashlib.sha256(os.path.normcase(os.path.abspath(path)).encode('utf-8')).hexdigest()

def atomic_json(path,data):
    path=Path(path)
    fd,temp=tempfile.mkstemp(prefix='.lib-',suffix='.tmp',dir=path.parent)
    try:
        with os.fdopen(fd,'w',encoding='utf-8') as stream:
            json.dump(data,stream,ensure_ascii=False,indent=2); stream.flush(); os.fsync(stream.fileno())
        os.replace(temp,path)
    finally:
        if os.path.exists(temp): os.unlink(temp)

class Catalog:
    def __init__(self,legacy=None): self.legacy=Path(legacy) if legacy else None
    def load(self,folder):
        folder=Path(folder); path=folder/'libdata.json'
        if not path.exists() and (folder/'lib.json').exists():path=folder/'lib.json'
        if path.exists():
            data=json.loads(path.read_text(encoding='utf-8-sig'))
            if not isinstance(data,dict) or not isinstance(data.get('books'),dict):
                raise ValueError(f'{path} 格式无效，原文件已保留，请修复后重试')
        else:
            data={'version':1,'books':{}}
            if self.legacy and self.legacy.exists():
                with closing(sqlite3.connect(self.legacy.resolve().as_uri()+'?mode=ro',uri=True)) as db:
                    for bid,p,slot,x,y in db.execute('SELECT id,path,slot,x,y FROM books WHERE room=?',(identity(folder),)):
                        data['books'][bid]={'name':Path(p).name,'slot':slot,'x':x,'y':y}
        return data
    def pack(self,data):
        ordered=sorted(data['books'].items(),key=lambda pair:(pair[1].get('order',pair[1].get('slot',10**9)),pair[1]['name'].casefold()))
        row=0;used=0.0
        for order,(bid,b) in enumerate(ordered):
            hint=b.get('row_hint')
            if isinstance(hint,int) and hint>row:row=hint;used=0.0
            width=max(.125,min(MAX_WIDTH,(b.get('pages') or 300)/300))
            gap=BOOK_GAP if used else 0.0
            if used+gap+width>ROW_WIDTH+1e-9:row+=1;used=0.0;gap=0.0
            used+=gap
            b.update(order=order,slot=order,width=width,shelf=row//6,row=row%6,offset=round(used,6))
            used+=width
        data.update(version=2,rows=6,row_width=ROW_WIDTH,book_gap=BOOK_GAP,standard_pages=300)
        data.pop('columns',None);data.pop('capacity',None)
        data['shelf_count']=max(1,row//6+1)
        return data
    def save(self,folder,data):
        self.pack(data);atomic_json(Path(folder)/'libdata.json',data)
    def sync(self,folder):
        folder=Path(folder);data=self.load(folder);original=json.dumps(data,sort_keys=True)
        files=sorted((p for p in folder.iterdir() if p.is_file() and p.suffix.lower() in BOOK_EXTENSIONS),key=lambda p:p.name.casefold())
        byname={b.get('name'):b for b in data['books'].values() if isinstance(b,dict)}
        records={};next_order=max((b.get('order',b.get('slot',0)) for b in byname.values()),default=-1)+1
        for p in files:
            bid=identity(p);item=dict(data['books'].get(bid) or byname.get(p.name) or {})
            order=item.get('order',item.get('slot'))
            if not isinstance(order,int) or order<0:order=next_order;next_order+=1
            item.update(name=p.name,path=str(p),order=order)
            st=p.stat();fingerprint=[st.st_size,st.st_mtime_ns]
            if item.get('fingerprint')!=fingerprint or 'pages' not in item:
                import pymupdf
                try:
                    with pymupdf.open(p) as doc:
                        if doc.needs_pass:raise ValueError('加密 PDF')
                        item['pages']=doc.page_count;item['pages_estimated']=bool(doc.is_reflowable);item.pop('page_error',None)
                except Exception as ex:item['pages']=None;item['page_error']=str(ex)
                item['fingerprint']=fingerprint
            records[bid]=item
        data['books']=records;self.pack(data)
        if not (folder/'libdata.json').exists() or json.dumps(data,sort_keys=True)!=original:self.save(folder,data)
        return data
    def scan(self,folder):
        data=self.sync(folder)
        return [(Path(folder)/b['name'],b['order']) for b in sorted(data['books'].values(),key=lambda b:b['order'])]
    def position(self,p):
        b=self.sync(Path(p).parent)['books'][identity(p)];return b.get('x'),b.get('y')
    def move(self,p,x,y):
        p=Path(p);data=self.sync(p.parent);data['books'][identity(p)].update(x=x,y=y);self.save(p.parent,data)
    def reorder(self,p,shelf,row,before=None):
        p=Path(p);data=self.sync(p.parent);bid=identity(p);book=data['books'][bid]
        if not isinstance(shelf,int) or not isinstance(row,int) or shelf<0 or shelf>=data['shelf_count'] or row not in range(6):raise ValueError('无效的书架层')
        target=[(key,b) for key,b in data['books'].items() if b['shelf']==shelf and b['row']==row and key!=bid]
        if sum(b['width'] for _,b in target)+book['width']+len(target)*BOOK_GAP>ROW_WIDTH+1e-9:raise ValueError('这一层剩余宽度不足，无法插入；原位置保持不变')
        ordered=[key for key,b in sorted(data['books'].items(),key=lambda pair:pair[1]['order']) if key!=bid]
        if before==bid:return
        if before is not None:
            if before not in {key for key,_ in target}:raise ValueError('插入位置已变化，请刷新后重试')
            index=ordered.index(before)
        elif target:index=ordered.index(max(target,key=lambda pair:pair[1]['order'])[0])+1
        else:index=next((i for i,key in enumerate(ordered) if data['books'][key]['shelf']*6+data['books'][key]['row']>shelf*6+row),len(ordered))
        for item in data['books'].values():item['row_hint']=item['shelf']*6+item['row']
        book['row_hint']=shelf*6+row
        ordered.insert(index,bid)
        for i,key in enumerate(ordered):data['books'][key]['order']=i
        self.save(p.parent,data)
    def rename(self,p,name):
        import copy,re
        p=Path(p)
        if not isinstance(name,str) or not name.strip():raise ValueError('改名失败：名称不能为空')
        name=name.strip()
        suffix=p.suffix
        if not name.lower().endswith(suffix.lower()):name+=suffix
        stem=name[:-len(suffix)]
        if not stem or name.endswith((' ','.')) or re.search(r'[<>:"/\\|?*\x00-\x1f]',name) or stem.endswith((' ','.')):
            raise ValueError('改名失败：名称含有 Windows 不允许的字符')
        if stem.split('.')[0].upper() in {'CON','PRN','AUX','NUL',*[f'COM{i}' for i in range(1,10)],*[f'LPT{i}' for i in range(1,10)]}:
            raise ValueError('改名失败：不能使用系统保留名称')
        target=p.with_name(name)
        if target==p:return p
        if target.exists():raise FileExistsError('改名失败：同名文件已存在')
        if not p.is_file():raise FileNotFoundError('改名失败：原文件不存在')
        data=copy.deepcopy(self.load(p.parent));old=identity(p);new=identity(target)
        record=data['books'].pop(old,None)
        if record is not None:
            record.update(name=name,path=str(target));data['books'][new]=record
        p.rename(target)
        try:self.save(p.parent,data)
        except Exception as ex:
            try:target.rename(p)
            except Exception as rollback:raise OSError(f'布局保存失败且文件名恢复失败：{ex}；{rollback}') from ex
            raise OSError(f'改名失败，原文件名已恢复：{ex}') from ex
        return target
    def transfer(self,p,folder):
        """Exclusive destination creation: never overwrite, unlink source only after copy and metadata succeed."""
        p=Path(p);folder=Path(folder);dest=folder/p.name
        if not p.is_file():raise FileNotFoundError(str(p))
        if identity(p.parent)==identity(folder):return dest
        if not folder.is_dir():raise ValueError('目标文件夹不存在')
        self.sync(p.parent);self.sync(folder)
        created=False
        try:
            with p.open('rb') as source, dest.open('xb') as target:
                created=True; before=os.fstat(source.fileno())
                shutil.copyfileobj(source,target,1024*1024);target.flush();os.fsync(target.fileno())
                after=os.fstat(source.fileno())
                if before.st_size!=after.st_size or before.st_mtime_ns!=after.st_mtime_ns or target.tell()!=after.st_size:
                    raise OSError('复制期间源文件发生变化，已取消移动')
            shutil.copystat(p,dest)
            self.sync(folder)
            p.unlink()
        except Exception:
            if created and p.exists():
                dest.unlink(missing_ok=True)
                try:self.sync(folder)
                except Exception:pass
            raise
        try:self.sync(p.parent)
        except Exception:pass # Missing-source records are reconciled on the next room scan.
        return dest
