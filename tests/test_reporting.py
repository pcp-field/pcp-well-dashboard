import unittest
from analysis import load_rows
from reporting import build_report

class ReportTests(unittest.TestCase):
    def test_report_uses_data_and_escapes_input(self):
        rows=load_rows(b'well_name,wear_rate,pump_speed_rpm,tubing_liner_source\n<script>,12,150,HDPE Liner\n')
        html=build_report(rows,rows,'Synthetic example',(150,150),['HDPE Liner'],'<x>').decode()
        self.assertIn('12.00',html)
        self.assertIn('SYNTHETIC EXAMPLE',html)
        self.assertIn('&lt;script&gt;',html)
        self.assertNotIn('<script>',html)
        self.assertIn('Not available',html)
        self.assertIn('PIPESIM 2023',html)
        with self.assertRaises(ValueError):build_report(rows,[], 'Upload CSV',(150,150),[], '')
