"""
Test the open_jpm.py
"""

import unittest2
from datetime import datetime
from xlrd import open_workbook
from trade_converter.utility import get_current_path
from trade_converter.port_12307 import data_field_begins, read_data_fields, \
                                        read_line, validate_trade_info, \
                                        InvalidTradeInfo



class TestPort12307(unittest2.TestCase):

    def __init__(self, *args, **kwargs):
        super(TestPort12307, self).__init__(*args, **kwargs)

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



    def test_data_field_begins(self):
        ws = self.get_worksheet('\\samples\\12307-20161111.xls')
        for row in range(7):
            if row < 6:
                self.assertFalse(data_field_begins(ws, row))
            if row == 6:
                self.assertTrue(data_field_begins(ws, row))



    def test_read_data_fields(self):
        ws = self.get_worksheet('\\samples\\12307-20161111.xls')
        fields = read_data_fields(ws, 6)
        self.assertEqual(len(fields), 26)
        self.assertEqual(fields[0], 'Acct#')
        self.assertEqual(fields[25], 'UnitPrice Flag')
        self.assertEqual(fields[21], 'Net Setl')
        self.assertEqual(fields[12], 'Units')



    def test_read_line1(self):
        """
        1st trade in \\samples\\12307-20161111.xls
        """
        ws = self.get_worksheet('\\samples\\12307-20161111.xls')
        fields = read_data_fields(ws, 6)
        trade_info = read_line(ws, 7, fields)
        self.verify_trade1(trade_info)
        try:
            validate_trade_info(trade_info)
        except:
            self.fail('trade validation failed')

        trade_info['Fees'] = trade_info['Fees'] + 0.001
        with self.assertRaises(InvalidTradeInfo):
            validate_trade_info(trade_info)



    def test_read_line2(self):
        """
        5th trade in \\samples\\12307-20161111.xls
        """
        ws = self.get_worksheet('\\samples\\12307-20161111.xls')
        fields = read_data_fields(ws, 6)
        trade_info = read_line(ws, 11, fields)
        self.verify_trade2(trade_info)
        try:
            validate_trade_info(trade_info)
        except:
            self.fail('trade validation failed')

        trade_info['Net Setl'] = trade_info['Net Setl'] - 0.001
        with self.assertRaises(InvalidTradeInfo):
            validate_trade_info(trade_info)



    def verify_trade1(self, trade_info):
        """
        1st trade in \\samples\\12307-20161111.xls
        """
        self.assertEqual(len(trade_info), 26)
        self.assertEqual(trade_info['Acct#'], '12307')
        self.assertEqual(trade_info['Setl Dt'], datetime(2016,11,15))
        self.assertEqual(trade_info['Units'], 174000)
        self.assertAlmostEqual(trade_info['Fees'], 2698.22)
        self.assertEqual(trade_info['UnitPrice Flag'], 'no')



    def verify_trade2(self, trade_info):
        """
        5th trade in \\samples\\12307-20161111.xls
        """
        self.assertEqual(len(trade_info), 26)
        self.assertEqual(trade_info['Acct#'], '12307')
        self.assertEqual(trade_info['Trd Dt'], datetime(2016,11,11))
        self.assertAlmostEqual(trade_info['Unit Price'], 22.3865)
        self.assertAlmostEqual(trade_info['Fees'], 861.88)
        self.assertEqual(trade_info['Trade#'], '5140')