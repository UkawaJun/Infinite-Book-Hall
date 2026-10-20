import json, tempfile, unittest
from pathlib import Path
from unittest.mock import patch
import main
class BridgeTests(unittest.TestCase):
 def test_settings_lazy_overview_and_walk(self):
  previous_base,previous_data=main.BASE,main.DATA
  with tempfile.TemporaryDirectory() as directory:
   root=Path(directory);main.BASE=root;main.DATA=root/'data';(root/'room').mkdir();(root/'room'/'not-a-real.pdf').touch()
   (root/'personal.json').write_text(json.dumps({'entrances':[]}),encoding='utf-8');bridge=main.Bridge(None)
   try:
    settings={'entrances':[{'name':'Room','path':'room'},{'name':'Offline','path':'missing'}]}
    result=json.loads(bridge.call('saveSettings',json.dumps(settings)));self.assertEqual(result['mode'],'maze')
    self.assertEqual(json.loads((root/'personal.json').read_text())['entrances'],settings['entrances'])
    self.assertEqual(result['layout'],json.loads(bridge.call('refresh','{}'))['layout'])
    entry=result['entries'][0];self.assertIn('error',json.loads(bridge.call('enter',json.dumps({'id':entry['id']}))))
    maze=result['layout'];target=maze['placements'][entry['id']];n=maze['size'];queue=[(0,[])];seen={0};route=[]
    while queue:
     cell,path=queue.pop(0)
     if cell==target:route=path;break
     for direction,wall in enumerate(maze['walls'][cell]):
      other=cell+[-n,1,n,-1][direction]
      if not wall and other not in seen:seen.add(other);queue.append((other,path+[direction]))
    for direction in route:bridge.call('walk',json.dumps({'direction':direction}))
    result=json.loads(bridge.call('enter',json.dumps({'id':entry['id']})));self.assertEqual(result['mode'],'shelves')
    bid=result['books'][0]['id']
    with patch('main.subprocess.Popen') as explorer,patch('main.os.startfile') as opener:
     self.assertEqual(json.loads(bridge.call('reveal',json.dumps({'id':bid}))),{})
     explorer.assert_called_once_with(['explorer.exe','/select,',str(root/'room'/'not-a-real.pdf')]);opener.assert_called_once_with(str(root/'room'/'not-a-real.pdf'))
    self.assertNotIn('cover',result['books'][0]);self.assertIsNone(bridge.pool);self.assertTrue((root/'room'/'libdata.json').exists())
   finally:bridge.close();main.BASE=previous_base;main.DATA=previous_data
class NavigationTests(unittest.TestCase):
 def test_child_start_parent_node_and_same_folder_shelf(self):
  previous_base,previous_data=main.BASE,main.DATA
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);a=root/'A';b=a/'B';b.mkdir(parents=True);(a/'book.pdf').touch();main.BASE=root;main.DATA=root/'data'
   (root/'personal.json').write_text(json.dumps({'entrances':[{'name':'A','path':str(a)}]}))
   bridge=main.Bridge(None)
   def call(action,**data):return json.loads(bridge.call(action,json.dumps(data)))
   try:
    lobby=call('home');aid=lobby['entries'][0]['id'];bridge.positions['lobby']=lobby['layout']['placements'][aid]
    room=call('enter',id=aid);self.assertEqual(room['player'],0)
    bid=next(e['id'] for e in room['entries'] if e['name']=='B');node=room['layout']['placements'][bid];bridge.positions[bridge.roomkey]=node
    call('enter',id=bid);back=call('back');self.assertEqual(back['player'],node)
    direct=next(e['id'] for e in back['entries'] if e['name']=='本层书架');node=back['layout']['placements'][direct];bridge.positions[bridge.roomkey]=node
    call('enter',id=direct);self.assertEqual(call('back')['player'],node)
    call('back');again=call('enter',id=aid);self.assertEqual(again['player'],0)
   finally:bridge.close();main.BASE=previous_base;main.DATA=previous_data
if __name__=='__main__':unittest.main()

class EntranceMergeTests(unittest.TestCase):
 def test_nested_paths_keep_room_metadata_and_same_names_distinct(self):
  previous_base,previous_data=main.BASE,main.DATA
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);(root/'A'/'B').mkdir(parents=True);(root/'Other').mkdir();main.BASE=root;main.DATA=root/'data'
   bridge=main.Bridge(None)
   try:
    entries=[{'name':'自习室','path':'A/B','type':'furniture'},{'name':'自习室','path':'Other'},{'name':'图书室','path':'A'},{'name':'重复','path':'A/.'}]
    result=json.loads(bridge.call('saveSettings',json.dumps({'entrances':entries})))
    self.assertEqual(len(result['entries']),2)
    self.assertEqual([e['path'] for e in bridge.cfg['entrances']],['Other','A'])
    bridge.current={'name':'图书室','path':'A'}
    room=bridge.state();child=bridge.entries[room['entries'][0]['id']]
    self.assertEqual(child['type'],'furniture');self.assertEqual(child['name'],'自习室')
    bridge.books['test']=root/'A'/'book.pdf';bridge.books['test'].touch()
    with patch('main.subprocess.Popen') as explorer,patch('main.os.startfile') as opener:
     self.assertEqual(json.loads(bridge.call('folder','{"id":"test"}')),{})
     explorer.assert_called_once();opener.assert_not_called()
   finally:bridge.close();main.BASE=previous_base;main.DATA=previous_data
