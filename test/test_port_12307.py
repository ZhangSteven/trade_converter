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
                                        convert_datetime_to_string, get_geneva_investment_id, \
                                        get_trade_expenses, fix_duplicate_key_value, \
                                        convert12307



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
        # try:
        #     print('hash value = {0}'.format(self.hash_string_to_int(keys[3])))
        # except:
        #     self.fail('invalid hash string: {0}'.format(keys[3]))



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



    def test_get_trade_expenses(self):
        """
        1st trade in \\samples\\12307-20161111.xls
        """
        ws = self.get_worksheet('\\samples\\12307-20161111.xls')
        fields = read_data_fields(ws, 6)
        trade_info = read_line(ws, 7, fields)
        trade_expenses = get_trade_expenses(trade_info)
        self.verify_trade_expense(trade_expenses)



    def test_fix_duplicate_key_value(self):
        records = []
        records.append({'KeyValue':'x', 'v':10})
        records.append({'KeyValue':'x', 'v':20})
        records.append({'KeyValue':'x', 'v':30})

        try:
            fix_duplicate_key_value(records)
            self.assertEqual(records[0], {'KeyValue':'x', 'v':10})
            self.assertEqual(records[1], {'KeyValue':'x_1', 'v':20})
            self.assertEqual(records[2], {'KeyValue':'x_2', 'v':30})

        except:
            self.fail()


    def test_fix_duplicate_key_value2(self):
        records = []
        records.append({'KeyValue':'x', 'v':10})
        records.append({'KeyValue':'y', 'v':20})
        records.append({'KeyValue':'x', 'v':30})
        records.append({'KeyValue':'x_1', 'v':40})

        try:
            fix_duplicate_key_value(records)
            self.assertEqual(records[0], {'KeyValue':'x', 'v':10})
            self.assertEqual(records[1], {'KeyValue':'y', 'v':20})
            self.assertEqual(records[2], {'KeyValue':'x_1', 'v':30})
            self.assertEqual(records[3], {'KeyValue':'x_1_1', 'v':40})
        except:
            self.fail()



    def test_convert12307(self):
        file = get_current_path() + '\\samples\\12307-20161111.xls'
        files = [file]
        records = convert12307(files)
        self.assertEqual(len(records), 5)
        self.verify_record1(records[0])
        self.verify_record2(records[4])



    def test_convert12307_2(self):
        file1 = get_current_path() + '\\samples\\12307-20161111.xls'
        file2 = get_current_path() + '\\samples\\12307-20161116.xls'
        files = [file1, file2]
        records = convert12307(files)
        self.assertEqual(len(records), 7)
        self.verify_record1(records[0])
        self.verify_record2(records[4])
        self.verify_record3(records[6])



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



    def verify_trade_expense(self, trade_expenses):
        self.assertEqual(len(trade_expenses), 5)
        
        expense_code, expense_value = trade_expenses[0]
        self.assertEqual(expense_code, 'CommissionTradeExpense')
        self.assertAlmostEqual(expense_value, 52562.58)

        expense_code, expense_value = trade_expenses[1]
        self.assertEqual(expense_code, 'Stamp_Duty')
        self.assertAlmostEqual(expense_value, 35042)

        expense_code, expense_value = trade_expenses[2]
        self.assertEqual(expense_code, 'Exchange_Fee')
        self.assertAlmostEqual(expense_value, 0)

        expense_code, expense_value = trade_expenses[3]
        self.assertEqual(expense_code, 'Transaction_Levy')
        self.assertAlmostEqual(expense_value, 0)

        expense_code, expense_value = trade_expenses[4]
        self.assertEqual(expense_code, 'Misc_Fee')
        self.assertAlmostEqual(expense_value, 2698.22)



    def verify_record1(self, record):
        """
        1st record from \\samples\\12307-20161111.xls
        """
        self.assertEqual(len(record), 27)
        self.assertEqual(record['RecordType'], 'Sell')
        self.assertEqual(record['Portfolio'], '12307')
        self.assertEqual(record['EventDate'], '2016-11-11')
        self.assertEqual(record['ActualSettleDate'], '2016-11-15')
        self.assertEqual(record['Quantity'], 174000)
        self.assertAlmostEqual(record['Price'], 201.3892)
        self.verify_trade_expense(record['trade_expenses'])



    def verify_record2(self, record):
        """
        5th record from \\samples\\12307-20161111.xls
        """
        self.assertEqual(len(record), 27)
        self.assertEqual(record['RecordType'], 'Sell')
        self.assertEqual(record['Investment'], '3606 HK')
        self.assertEqual(record['EventDate'], '2016-11-11')
        self.assertEqual(record['SettleDate'], '2016-11-15')
        self.assertEqual(record['Quantity'], 500000)
        self.assertAlmostEqual(record['Price'], 22.3865)



    def verify_record3(self, record):
        """
        2nd record from \\samples\\12307-20161116.xls
        """
        self.assertEqual(len(record), 27)
        self.assertEqual(record['RecordType'], 'Buy')
        self.assertEqual(record['Investment'], '1880 HK')
        self.assertEqual(record['EventDate'], '2016-11-16')
        self.assertEqual(record['ActualSettleDate'], '2016-11-18')
        self.assertEqual(record['Quantity'], 540000)
        self.assertAlmostEqual(record['Price'], 4.4039)
