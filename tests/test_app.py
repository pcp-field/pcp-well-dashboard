"""Smoke tests use synthetic data only, including on machines with private data."""
import unittest
from pathlib import Path
from streamlit.testing.v1 import AppTest

class InterfaceTests(unittest.TestCase):
    def test_demo_and_filters(self):
        at=AppTest.from_file(str(Path(__file__).resolve().parents[1] / 'app.py'), default_timeout=40)
        at.session_state['source']='بيانات تجريبية'
        at.run()
        self.assertFalse(at.exception)
        self.assertEqual(at.metric[0].value,'8')
        at.radio(key='order').set_value('الأقل أولًا').run()
        self.assertFalse(at.exception)
        at.multiselect(key='liner_filter').set_value(['HDPE Liner']).run()
        self.assertEqual(at.metric[0].value,'3')
        self.assertFalse(at.exception)
        at.text_input(key='search').set_value('NO-MATCH').run()
        self.assertTrue(at.warning)
        self.assertFalse(at.exception)

if __name__=='__main__':unittest.main()
