"""
Test the open_jpm.py
"""

import unittest2
from datetime import datetime
from xlrd import open_workbook
from trade_converter.utility import get_current_path
from trade_converter.port_ft import read_data_fields, read_line, \
                                    validate_trade_info



class TestPortFT(unittest2.TestCase):

    def __init__(self, *args, **kwargs):
        super(TestPortFT, self).__init__(*args, **kwargs)

    def setUp(self):
        """
            Run before a test function
        """
        pass



    def tearDown(self):
        """
            Run after a test finishes
        """
        pass



    def get_worksheet(self, filename):
        filename = get_current_path() + filename
        wb = open_workbook(filename=filename)
        ws = wb.sheet_by_index(0)
        return ws



    def test_read_line(self):
        ws = self.get_worksheet('\\samples\\sample_FT.xlsx')
        fields = read_data_fields(ws, 0)
        trade_info = read_line(ws, 1, fields)
        self.verify_trade_info1(trade_info)
        validate_trade_info(trade_info)

        trade_info = read_line(ws, 3, fields)
        self.verify_trade_info2(trade_info)
        validate_trade_info(trade_info)

        trade_info = read_line(ws, 17, fields)
        self.verify_trade_info3(trade_info)
        validate_trade_info(trade_info)



    def verify_trade_info1(self, trade_info):
        """
        1st position in sample_FT.xlsx
        """
        self.assertEqual(trade_info['ACCT_ACNO'], '21815')
        self.assertEqual(trade_info['TRDDATE'], datetime(2016,8,4))
        self.assertEqual(trade_info['QTY'], 5000000)
        self.assertEqual(trade_info['TRADEPRC'], '')
        self.assertEqual(trade_info['SCTYID_ISIN'], 'USG21184AB52')
        self.assertEqual(trade_info['FXRATE'], 1)



    def verify_trade_info2(self, trade_info):
        """
        3rd position in sample_FT.xlsx
        """
        self.assertEqual(trade_info['SCTYID_SMSEQ'], '')
        self.assertEqual(trade_info['ENTRDATE'], datetime(2016,8,15))
        self.assertEqual(trade_info['QTY'], '')
        self.assertEqual(trade_info['GROSSBAS'], 71250)
        self.assertEqual(trade_info['ACCRBAS'], '')
        self.assertEqual(trade_info['LCLCCY'], 'USD')



    def verify_trade_info3(self, trade_info):
        """
        17th position in sample_FT.xlsx (BIDU US)
        """
        self.assertEqual(trade_info['SCTYNM'], 'BAIDU INC ADR NPV')
        self.assertEqual(trade_info['STLDATE'], datetime(2016,11,16))
        self.assertEqual(trade_info['QTY'], 35000)
        self.assertEqual(trade_info['ACCRBAS'], 0)
        self.assertAlmostEqual(trade_info['TRADEPRC'], 162.4842)
        self.assertAlmostEqual(trade_info['FXRATE'], 0.1288917245)
