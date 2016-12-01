"""
Test the open_jpm.py
"""

import unittest2
from datetime import datetime
from xlrd import open_workbook
from trade_converter.utility import get_current_path
from trade_converter.port_12307 import data_field_begins, read_data_fields, \
                                        read_line, validate_trade_info, \
                                        InvalidTradeInfo, create_record_key_value, \
                                        convert_datetime_to_string, get_geneva_investment_id



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



    def test_create_record_key_value(self):
        """
        1st trade in \\samples\\12307-20161111.xls
        """
        ws = self.get_worksheet('\\samples\\12307-20161111.xls')
        fields = read_data_fields(ws, 6)
        trade_info = read_line(ws, 7, fields)

        key_value = create_record_key_value(trade_info)
        keys = key_value.split('_')
        self.assertEqual(keys[0], '12307')
        self.assertEqual(keys[1], '2016-11-11')
        self.assertEqual(keys[2], 'Sell')
        try:
            print('hash value = {0}'.format(self.hash_string_to_int(keys[3])))
        except:
            self.fail('invalid hash string: {0}'.format(keys[3]))



    def test_get_geneva_investment_id(self):
        lookup_file = get_current_path() + '\\samples\\sample_investmentLookup.xls'
        # investment_lookup = get_geneva_investment_id.i_lookup
        # self.assertEqual(investment_lookup, 28)
        trade_info = {}
        trade_info['ISIN'] = 'US01609W1027' # fist
        name, ticker = get_geneva_investment_id(trade_info)
        self.assertEqual(ticker, 'BABA US')

        trade_info['ISIN'] = 'KYG981491007' # last
        name, ticker = get_geneva_investment_id(trade_info)
        self.assertEqual(ticker, '1128 HK')

        trade_info['ISIN'] = 'HK0941009539'
        name, ticker = get_geneva_investment_id(trade_info)
        self.assertEqual(ticker, '941 HK')
        self.assertEqual(name, 'CHINA MOBILE LTD')

        trade_info['ISIN'] = 'KYG5636C1078'
        name, ticker = get_geneva_investment_id(trade_info)
        self.assertEqual(ticker, '3339 HK')
        self.assertEqual(name, 'LONKING HOLDINGS LTD')



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



    def hash_string_to_int(self, hash_string):
        if hash_string[0] == 'n':
            hash_string = hash_string[1:]

        return int(hash_string)