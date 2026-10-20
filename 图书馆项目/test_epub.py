import tempfile,unittest,zipfile
from pathlib import Path
from catalog import Catalog,identity
from cover_worker import render_cover

class EpubTests(unittest.TestCase):
 def test_scan_cover_rename_and_transfer(self):
  with tempfile.TemporaryDirectory() as d:
   room=Path(d);p=room/'sample.epub'
   with zipfile.ZipFile(p,'w') as z:
    z.writestr('mimetype','application/epub+zip')
    z.writestr('META-INF/container.xml','<container xmlns="urn:oasis:names:tc:opendocument:xmlns:container" version="1.0"><rootfiles><rootfile full-path="content.opf" media-type="application/oebps-package+xml"/></rootfiles></container>')
    z.writestr('content.opf','<package xmlns="http://www.idpf.org/2007/opf" version="2.0" unique-identifier="uid"><metadata xmlns:dc="http://purl.org/dc/elements/1.1/"><dc:title>Test</dc:title><dc:identifier id="uid">test</dc:identifier><dc:language>en</dc:language></metadata><manifest><item id="one" href="one.xhtml" media-type="application/xhtml+xml"/></manifest><spine><itemref idref="one"/></spine></package>')
    z.writestr('one.xhtml','<html xmlns="http://www.w3.org/1999/xhtml"><head><title>Book</title></head><body><h1>EPUB TEST</h1><p>Reading room.</p></body></html>')
   catalog=Catalog();book=catalog.sync(room)['books'][identity(p)]
   self.assertGreater(book['pages'],0);self.assertTrue(book['pages_estimated'])
   self.assertTrue(render_cover(str(p),str(room/'cover.jpg')).startswith('data:image/jpeg;base64,'))
   renamed=catalog.rename(p,'renamed');self.assertEqual(renamed.suffix,'.epub')
   dest=room/'dest';dest.mkdir();moved=catalog.transfer(renamed,dest)
   self.assertTrue(moved.exists());self.assertFalse(renamed.exists());self.assertIn(identity(moved),catalog.sync(dest)['books'])
