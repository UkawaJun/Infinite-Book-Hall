import tempfile,unittest,json
from pathlib import Path
from usage_clock import UsageClock
class UsageTests(unittest.TestCase):
 def test_save_recovery_and_offline_not_counted(self):
  with tempfile.TemporaryDirectory() as d:
   now=[0];clock=UsageClock(d,lambda:now[0]);now[0]=3661;clock.save()
   clock.stop.set();clock.thread.join() # simulate abrupt exit without final save
   resumed=UsageClock(d,lambda:100000);self.assertEqual(resumed.seconds(),3661);resumed.close();resumed.close()
   data=json.loads((Path(d)/'usage.json').read_text());self.assertEqual((data['D'],data['H'],data['M']),(0,1,1))
