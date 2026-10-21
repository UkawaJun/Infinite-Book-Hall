import json, tempfile, unittest
from pathlib import Path
from cash_cache import CashCache
from cover_worker import render_cover
from test_catalog import pdf
class CacheTests(unittest.TestCase):
 def test_3000_to_1500_lru(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);p=root/'a.pdf';p.touch();cache=CashCache(root/'CASH')
   for i in range(3000):
    key=f'{i:064x}';(cache.root/(key+'.jpg')).write_bytes(b'x');cache.add(key,p)
   cache.touch(f'{0:064x}');key=f'{3000:064x}';(cache.root/(key+'.jpg')).write_bytes(b'x');cache.add(key,p);cache.flush()
   self.assertEqual(len(cache.entries),1500);self.assertEqual(len(list(cache.root.glob('*.jpg'))),1500);self.assertIn(f'{0:064x}',cache.entries);self.assertNotIn(f'{1:064x}',cache.entries)
   index=json.loads(cache.index.read_text());self.assertEqual(index['entries'][0]['key'],key);self.assertEqual(len(CashCache(cache.root).entries),1500)
 def test_jpeg_and_invalidation(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);p=root/'a.pdf';pdf(p,1);cache=CashCache(root/'CASH');key,_=cache.get(p)
   image=render_cover(str(p),str(cache.root/(key+'.jpg')));self.assertTrue(image.startswith('data:image/jpeg;base64,'));self.assertEqual((cache.root/(key+'.jpg')).read_bytes()[:2],b'\xff\xd8')
   cache.add(key,p);self.assertEqual(cache.get(p)[1],image);p.unlink();pdf(p,2);self.assertNotEqual(cache.key(p),key);self.assertIsNone(cache.get(p)[1])
if __name__=='__main__':unittest.main()
