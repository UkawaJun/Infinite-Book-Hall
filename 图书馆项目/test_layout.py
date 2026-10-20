import copy, unittest
from layout import plan
class LayoutTests(unittest.TestCase):
 def test_stable_and_connected(self):
  cfg={}; a=plan(cfg,'room',['a','b','c']); self.assertEqual(a,plan(cfg,'room',['c','b','a']))
  self.assertEqual(a,plan({},'room',['a','b','c']))
  self.assertNotEqual(a['seed'],plan(cfg,'room',['a','b','c','d'])['seed'])
  n=a['size']; seen={0}; pending=[0]
  while pending:
   cell=pending.pop()
   for d,offset in enumerate([-n,1,n,-1]):
    if not a['walls'][cell][d]:
     other=cell+offset
     self.assertFalse(a['walls'][other][(d+2)%4])
     if other not in seen:seen.add(other);pending.append(other)
  self.assertEqual(len(seen),n*n)
  self.assertEqual(len(set(a['placements'].values())),3)
if __name__=='__main__':unittest.main()
