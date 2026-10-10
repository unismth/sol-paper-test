import json,unittest
from pathlib import Path
from unittest.mock import Mock,patch
import paper_sol as p
import public_data

class CloudTests(unittest.TestCase):
    def rows(self):
        return [{'t':i*3600000,'T':(i+1)*3600000-1,'o':100+i,'h':102+i,'l':99+i,'c':101+i,'v':100+i} for i in range(288)]
    def test_only_public_endpoints(self):
        with patch.object(public_data.urllib.request,'urlopen') as request:
            for payload in ({'type':'clearinghouseState'},{'type':'order'},{'type':'withdraw'}):
                with self.assertRaises(ValueError):public_data.info(public_data.MAINNET,payload)
            request.assert_not_called()
    def test_causal_trend_filter(self):
        rows=self.rows();short=p.trend_filter(rows[:220]);full=p.trend_filter(rows)
        self.assertTrue(full(1,rows));self.assertFalse(full(-1,rows))
        self.assertFalse(full(1,rows[:199]))
        for side in (-1,1):self.assertEqual(short(side,rows[:220]),full(side,rows[:220]))
    def test_first_start_does_not_require_wallet(self):
        rows=self.rows();state=Mock(spec=Path);state.exists.return_value=False
        result=Path('result');stored={}
        with patch.object(p,'STATE',state),patch.object(p,'RESULT',result),patch.object(p.time,'time',return_value=(288*3600000+30000)/1000),patch.object(p,'info',return_value=rows),patch.object(p,'write',side_effect=lambda path,data:stored.__setitem__(path,data)):
            p.once()
        self.assertTrue(stored[result]['paper_only']);self.assertEqual(stored[result]['trades'],0)
    def test_wrong_version_is_rejected(self):
        state=Mock(spec=Path);state.exists.return_value=True;state.read_text.return_value=json.dumps({'strategy_version':'other'})
        with patch.object(p,'STATE',state),patch.object(p,'info') as request:
            with self.assertRaises(RuntimeError):p.once()
            request.assert_not_called()

if __name__=='__main__':unittest.main()
