import unittest
from execution_paper import closed_signal,make_pending,attempt_fill,simulate

def row(t,o=100,h=101,l=99,c=100):return {'t':t,'T':t+59999,'o':o,'h':h,'l':l,'c':c,'v':1}

class ExecutionTests(unittest.TestCase):
    def test_signal_requires_closed_history(self):
        history=[row(i*3600000,h=101,l=99,c=100) for i in range(20)]
        self.assertEqual(closed_signal(history),0)
        self.assertEqual(closed_signal(history+[row(20*3600000,h=104,c=103)]),1)
    def test_touch_does_not_fill(self):
        p=make_pending(1,100,100,0,'maker')
        self.assertIsNone(attempt_fill(p,row(0,l=p['limit']),.0003))
        self.assertEqual(attempt_fill(p,row(0,l=p['limit']*.9998),.0003),p['limit'])
    def test_limit_expires(self):
        p=make_pending(1,100,100,0,'maker')
        self.assertIsNone(attempt_fill(p,row(300000,l=95),.0003))
    def test_nonpassive_limit_rejected(self):
        self.assertIsNone(make_pending(1,100,99,0,'maker'))
    def test_forward_tracker_keeps_open_position(self):
        hours=[{'t':i*3600000,'T':(i+1)*3600000-1,'o':100,'h':101,'l':99,'c':100} for i in range(20)]
        hours.append({'t':20*3600000,'T':21*3600000-1,'o':100,'h':103,'l':100,'c':102})
        t=21*3600000
        r=simulate([row(t,o=102,h=102.1,l=101.9,c=102)],hours,[],start_ms=t,close_end=False)
        self.assertEqual(r['trades'],0);self.assertIsNotNone(r['open_position'])
        self.assertEqual(r['balance'],6.18)

    def test_future_hour_cannot_change_past_decision(self):
        hours=[{'t':i*3600000,'T':(i+1)*3600000-1,'o':100,'h':101,'l':99,'c':100} for i in range(20)]
        hours.append({'t':20*3600000,'T':21*3600000-1,'o':100,'h':103,'l':100,'c':102})
        future={'t':21*3600000,'T':22*3600000-1,'o':102,'h':10000,'l':1,'c':1}
        minutes=[row(21*3600000,o=102,h=102.1,l=101.9,c=102)]
        a=[];b=[]
        short=simulate(minutes,hours,[],start_ms=minutes[0]['t'],close_end=False,audit=a.append)
        long=simulate(minutes,hours+[future],[],start_ms=minutes[0]['t'],close_end=False,audit=b.append)
        self.assertEqual(short,long);self.assertEqual(a,b)
        self.assertTrue(all(x['latest_visible_hour_close_ms']<x['clock_ms'] for x in a))

    def test_fixed_notional_and_millisecond_funding(self):
        hours=[{'t':i*3600000,'T':(i+1)*3600000-1,'o':100,'h':101,'l':99,'c':100} for i in range(20)]
        hours.append({'t':20*3600000,'T':21*3600000-1,'o':100,'h':103,'l':100,'c':102})
        t=21*3600000
        minutes=[row(t,o=102,h=102.1,l=101.9,c=102)]
        r=simulate(minutes,hours,[{'time':t+3,'fundingRate':'.001'}],start_ms=t,close_end=False,position_notional=11)
        p=r['open_position'];self.assertGreaterEqual(p['notional'],10.01);self.assertLessEqual(p['notional'],11)
        self.assertAlmostEqual(p['funding'],p['qty']*102*.001)

if __name__=='__main__':unittest.main()
