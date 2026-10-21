import json, tempfile, unittest, sqlite3
from pathlib import Path
from unittest.mock import patch
from catalog import Catalog, identity
import pymupdf

def pdf(path,pages):
 with pymupdf.open() as doc:
  for _ in range(pages):doc.new_page()
  doc.save(path)

class Tests(unittest.TestCase):
 def test_width_packing_and_migration(self):
  c=Catalog();data={'books':{str(i):{'name':str(i),'pages':300,'slot':i*2} for i in range(91)}};c.pack(data)
  self.assertEqual(data['shelf_count'],2);self.assertEqual(data['books']['15']['row'],1);self.assertEqual(data['books']['90']['shelf'],1)
  data={'books':{'thin':{'name':'a','pages':1,'order':0},'normal':{'name':'b','pages':300,'order':1},'thick':{'name':'c','pages':9000,'order':2}}};c.pack(data)
  self.assertEqual([data['books'][i]['width'] for i in ['thin','normal','thick']],[.125,1,1.25])
  self.assertEqual(data['books']['thick']['offset'],1.205)
 def test_pages_cached_and_change_invalidates(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);book=p/'a.pdf';pdf(book,30);c=Catalog();b=c.sync(p)['books'][identity(book)];self.assertEqual(b['pages'],30)
   with patch('pymupdf.open',side_effect=AssertionError('unchanged PDF must not be reopened')):c.sync(p)
   book.unlink();pdf(book,450);self.assertEqual(c.sync(p)['books'][identity(book)]['width'],1.25)
   c.move(book,123,234);self.assertEqual(Catalog().position(book),(123,234))
 def test_insert_rejects_overflow_and_keeps_row(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);c=Catalog()
   for i in range(16):(p/f'{i:02}.pdf').touch()
   data=c.sync(p);before=(p/'libdata.json').read_bytes()
   with self.assertRaises(ValueError):c.reorder(p/'15.pdf',0,0)
   self.assertEqual((p/'libdata.json').read_bytes(),before)
   c.reorder(p/'00.pdf',0,1,identity(p/'15.pdf'))
   data=c.sync(p);self.assertEqual(data['books'][identity(p/'00.pdf')]['row'],1)
   self.assertLess(data['books'][identity(p/'00.pdf')]['order'],data['books'][identity(p/'15.pdf')]['order'])
   c.reorder(p/'00.pdf',0,5);self.assertEqual(c.sync(p)['books'][identity(p/'00.pdf')]['row'],5)
 def test_rename_success_and_failures(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);book=p/'original.pdf';pdf(book,300);c=Catalog();c.move(book,25,30);original=(p/'libdata.json').read_bytes()
   collision=p/'existing.pdf';collision.write_bytes(b'existing')
   with self.assertRaises(FileExistsError):c.rename(book,'existing.pdf')
   self.assertEqual((p/'libdata.json').read_bytes(),original);self.assertTrue(book.exists())
   with patch.object(Path,'rename',side_effect=PermissionError('locked')),patch.object(c,'save') as save:
    with self.assertRaises(PermissionError):c.rename(book,'new.pdf')
    save.assert_not_called()
   with patch.object(c,'save',side_effect=OSError('read-only metadata')):
    with self.assertRaises(OSError):c.rename(book,'new.pdf')
   self.assertTrue(book.exists());self.assertFalse((p/'new.pdf').exists());self.assertEqual((p/'libdata.json').read_bytes(),original)
   for name in ['../bad','CON','x/y','a?b']:
    with self.assertRaises(ValueError):c.rename(book,name)
   new=c.rename(book,'renamed');self.assertEqual(new.name,'renamed.pdf');self.assertFalse(book.exists());self.assertEqual(c.position(new),(25,30))
 def test_transfer_conflicts_and_failure(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);a=root/'a';b=root/'b';a.mkdir();b.mkdir();book=a/'book.pdf';book.write_bytes(b'important PDF')
   c=Catalog();c.move(book,30,40);c.transfer(book,b)
   self.assertFalse(book.exists());self.assertEqual((b/book.name).read_bytes(),b'important PDF')
   self.assertEqual(c.sync(a)['books'],{});self.assertEqual(len(c.sync(b)['books']),1)
   book.write_bytes(b'new')
   with self.assertRaises(FileExistsError):c.transfer(book,b)
   self.assertEqual(book.read_bytes(),b'new');self.assertEqual((b/book.name).read_bytes(),b'important PDF')
   other=a/'other.pdf';other.write_bytes(b'keep');real=c.sync
   def fail_after_copy(folder):
    if Path(folder)==b and (b/'other.pdf').exists():raise PermissionError('metadata write denied')
    return real(folder)
   with patch.object(c,'sync',side_effect=fail_after_copy):
    with self.assertRaises(PermissionError):c.transfer(other,b)
   self.assertEqual(other.read_bytes(),b'keep');self.assertFalse((b/'other.pdf').exists())
 def test_invalid_json_preserved(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);(p/'libdata.json').write_text('invalid')
   with self.assertRaises(ValueError):Catalog().sync(p)
   self.assertEqual((p/'libdata.json').read_text(),'invalid')
 def test_legacy_and_portable_records(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);book=p/'book.pdf';pdf(book,10);legacy=p/'old.sqlite'
   with sqlite3.connect(legacy) as db:
    db.execute('CREATE TABLE books(id TEXT,path TEXT,room TEXT,slot INTEGER,x REAL,y REAL)');db.execute('INSERT INTO books VALUES(?,?,?,?,?,?)',(identity(book),str(book),identity(p),95,45,65))
   db.close();data=Catalog(legacy).sync(p);self.assertEqual(data['books'][identity(book)]['order'],0)
   data['books']['old-id']=data['books'].pop(identity(book));(p/'libdata.json').write_text(json.dumps(data))
   self.assertEqual(Catalog().position(book),(45,65))
if __name__=='__main__':unittest.main()

class LegacyLayoutMigrationTests(unittest.TestCase):
 def test_legacy_layout_is_preserved_and_new_file_written(self):
  import tempfile,json
  from pathlib import Path
  from catalog import Catalog
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);book=root/'legacy.pdf';book.touch();old=root/'lib.json';old.write_text(json.dumps({'version':2,'books':{'old':{'name':book.name,'order':0,'x':37,'y':42}}}))
   original=old.read_bytes();Catalog().sync(root)
   self.assertTrue((root/'libdata.json').exists());self.assertEqual(old.read_bytes(),original)
   old.write_text('broken legacy file')
   record=next(iter(Catalog().sync(root)['books'].values()));self.assertEqual((record['x'],record['y']),(37,42))
