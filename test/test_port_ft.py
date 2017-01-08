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
        self.assertEqual(trade_info, None)

        trade_info = read_line(ws, 13, fields)
        self.verify_trade_info1(trade_info)
        validate_trade_info(trade_info)

        trade_info = read_line(ws, 17, fields)
        self.verify_trade_info2(trade_info)
        validate_trade_info(trade_info)



    def test_read_line2(self):
        ws = self.get_worksheet('\\samples\\sample_FT_12229.xls')
        fields = read_data_fields(ws, 0)

        trade_info = read_line(ws, 2, fields)
        self.verify_trade_info3(trade_info)
        validate_trade_info(trade_info)

        trade_info = read_line(ws, 5, fields)
        self.verify_trade_info4(trade_info)
        validate_trade_info(trade_info)



    def verify_trade_info1(self, trade_info):
        """
        13th position in sample_FT.xlsx
        """
        self.assertEqual(trade_info['SCTYID_ISIN'], 'XS1328315723')
        self.assertEqual(trade_info['ENTRDATE'], datetime(2016,6,14))
        self.assertEqual(trade_info['QTY'], 1000000)
        self.assertEqual(trade_info['GROSSBAS'], -1003000)
        self.assertAlmostEqual(trade_info['ACCRBAS'], -25690.97)
        self.assertEqual(trade_info['LCLCCY'], 'USD')
        self.assertAlmostEqual(trade_info['TRADEPRC'], 100.3)
        self.assertAlmostEqual(trade_info['FXRATE'], 1)



    def verify_trade_info2(self, trade_info):
        """
        17th position in sample_FT.xlsx (BIDU US)
        """
        self.assertEqual(trade_info['SCTYNM'], 'BAIDU INC ADR NPV')
        self.assertEqual(trade_info['STLDATE'], datetime(2016,11,16))
        self.assertEqual(trade_info['QTY'], 35000)
        self.assertEqual(trade_info['ACCRBAS'], 0)
        self.assertAlmostEqual(trade_info['TRADEPRC'], 162.4842)
        self.assertAlmostEqual(trade_info['FXRATE'], 0.1288917245)



    def verify_trade_info3(self, trade_info):
        """
        2nd position in sample_FT_12229.xls
        """
        self.assertEqual(trade_info['SCTYID_SEDOL'], 'B8BTZG2')
        self.assertEqual(trade_info['TRDDATE'], datetime(2013,6,21))
        self.assertEqual(trade_info['QTY'], 300000)
        self.assertAlmostEqual(trade_info['GROSSBAS'], -2163201.81)
        self.assertAlmostEqual(trade_info['ACCRBAS'], -14818.26)
        self.assertEqual(trade_info['LCLCCY'], 'USD')
        self.assertAlmostEqual(trade_info['TRADEPRC'], 92.942)
        self.assertAlmostEqual(trade_info['FXRATE'], 0.1288950475)



    def verify_trade_info4(self, trade_info):
        """
        5th position in sample_FT_12229.xls
        """
        self.assertEqual(trade_info['SCTYID_ISIN'], 'XS0545110354')
        self.assertEqual(trade_info['STLDATE'], datetime(2015,4,16))
        self.assertEqual(trade_info['QTY'], 500000)
        self.assertEqual(trade_info['PRINB'], 4382794.65)
        self.assertAlmostEqual(trade_info['RGLCCYCLS'], -4106.51)
        self.assertEqual(trade_info['LCLCCY'], 'USD')
        self.assertAlmostEqual(trade_info['TRADEPRC'], 113.1)
        self.assertAlmostEqual(trade_info['FXRATE'], 0.1290272635)

