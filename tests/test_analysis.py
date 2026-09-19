import unittest
from analysis import load_rows, summary, rank, groups, csv_bytes

HEADER='well_name,wear_rate,pump_speed_rpm,tubing_liner_source\n'
class AnalysisTests(unittest.TestCase):
    def setUp(self):
        self.rows=load_rows((HEADER+'A,0,160,HDPE Liner\nB,20,150,HDPE Liner\nC,80,250,No Liner/Coating\n').encode())
    def test_mean_and_groups(self):
        self.assertEqual(summary(self.rows)['count'],3)
        self.assertAlmostEqual(summary(self.rows)['mean_wear'],100/3)
        self.assertEqual(groups(self.rows)['HDPE Liner']['mean_wear'],10)
        self.assertEqual(groups(self.rows[:2])['No Liner/Coating'],None)
    def test_rank_numeric_and_zero(self):
        self.assertEqual([r['well_name'] for r in rank(self.rows,2)],['C','B'])
        self.assertEqual(rank(self.rows,1,False)[0]['wear_rate'],0)
    def test_invalid(self):
        for body in ['A,NaN,160,HDPE Liner\n','A,-1,160,HDPE Liner\n','A,1,160,Other\n','A,1,160,HDPE Liner\nA,2,160,HDPE Liner\n','']:
            with self.subTest(body=body), self.assertRaises(ValueError):load_rows((HEADER+body).encode())
        with self.assertRaises(ValueError):load_rows(b'well_name,wear_rate\nA,12\n')
    def test_utf8_and_export(self):
        data=csv_bytes(self.rows)
        self.assertEqual(load_rows(data),self.rows)
        self.assertEqual(summary([]),None)
    def test_formula_export(self):
        self.rows[0]['well_name']='=1+1'
        self.assertIn(b"'=1+1",csv_bytes(self.rows))

if __name__=='__main__':unittest.main()
