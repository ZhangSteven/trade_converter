"""
Test the open_jpm.py
"""

import unittest2
from datetime import datetime
from os.path import join
from trade_converter.utility import get_current_path
from small_program.read_file import read_file
from trade_converter.port_12734 import read_transaction_file, convert12734



class TestPort12734(unittest2.TestCase):

    def __init__(self, *args, **kwargs):
        super(TestPort12734, self).__init__(*args, **kwargs)

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



    def test_read_transaction_file(self):
        file = join(get_current_path(), 'samples', 'bond_order_sample1.xls')
        output_list = []
        error_list = []
        read_transaction_file(file, output_list, error_list)
        self.assertEqual(len(output_list), 4)
        self.assertEqual(len(error_list), 0)
        self.verify_bond_order1(output_list[0])
        self.verify_bond_order2(output_list[3])



    def test_read_transaction_file2(self):
        file = join(get_current_path(), 'samples', 'bond_order_error1.xls')
        output_list = []
        error_list = []
        read_transaction_file(file, output_list, error_list)
        self.assertEqual(len(output_list), 0)
        self.assertEqual(len(error_list), 1)



    def test_read_transaction_file3(self):
        file = join(get_current_path(), 'samples', 'bond_order_error2.xls')
        output_list = []
        error_list = []
        read_transaction_file(file, output_list, error_list)
        self.assertEqual(len(output_list), 0)
        self.assertEqual(len(error_list), 1)



    def test_read_transaction_file4(self):
        file = join(get_current_path(), 'samples', 'bond_order_error3.xls')
        output_list = []
        error_list = []
        read_transaction_file(file, output_list, error_list)
        self.assertEqual(len(output_list), 0)
        self.assertEqual(len(error_list), 1)



    def test_read_transaction_file5(self):
        file = join(get_current_path(), 'samples', 'bond_order_sample2.xls')
        output_list = []
        error_list = []
        read_transaction_file(file, output_list, error_list)
        self.assertEqual(len(output_list), 1)
        self.assertEqual(len(error_list), 0)
        self.verify_bond_order3(output_list[0])



    def test_read_transaction_file6(self):
        file = join(get_current_path(), 'samples', 'bond_order_error4.xls')
        output_list = []
        error_list = []
        read_transaction_file(file, output_list, error_list)
        self.assertEqual(len(output_list), 1)
        self.assertEqual(len(error_list), 1)
        self.verify_bond_order4(output_list[0])
        self.assertEqual(error_list[0], 15) # error occurred on row 15



    def test_convert_12734(self):
        files = [get_current_path() + '\\samples\\bond_order_sample1.xls']
        records = convert12734(files)
        self.assertEqual(len(records), 4)
        self.verify_record1(records[0])
        self.verify_record2(records[2])
        self.verify_record3(records[3])



    def verify_bond_order1(self, record):
        self.assertEqual(len(record), 18)
        self.assertEqual(record['Form Serial No.'], 'GFI-10-1215')
        self.assertEqual(record['Item No.'], 1)
        self.assertEqual(record['Buy/Sell'], 'Buy')
        self.assertEqual(record['Par Value'], 2700000)
        self.assertAlmostEqual(record['Price (%)'], 98.84)
        self.assertEqual(record['Trade Date'], datetime(2010,12,15))



    def verify_bond_order2(self, record):
        self.assertEqual(len(record), 18)
        self.assertEqual(record['Security Code'], 'XS0556302163')
        self.assertEqual(record['Security Name'], 'Chong Hing 6% 4 Nov 2020')
        self.assertEqual(record['Currency'], 'US$')
        self.assertEqual(record['Par Value'], 2700000)
        self.assertAlmostEqual(record['Price (%)'], 99.62)
        self.assertEqual(record['Trade Date'], datetime(2010,12,15))



    def verify_bond_order3(self, record):
        self.assertEqual(len(record), 18)
        self.assertEqual(record['Security Code'], 'HK0000134780')
        self.assertEqual(record['Security Name'], 'Far East Horizon 5.75% 7 Oct 2017')
        self.assertEqual(record['Currency'], 'CNY')
        self.assertEqual(record['Par Value'], 900000000)
        self.assertAlmostEqual(record['Price (%)'], 98.989)
        self.assertEqual(record['Trade Date'], datetime(2012,12,28))



    def verify_bond_order4(self, record):
        self.assertEqual(len(record), 18)
        self.assertEqual(record['Security Code'], 'XS0852986313')
        self.assertEqual(record['Security Name'], 'CHINA OVERSEAS 5.35% 11/15/42')
        self.assertEqual(record['Currency'], 'USD')
        self.assertEqual(record['Par Value'], 1200000)
        self.assertAlmostEqual(record['Price (%)'], 87.86)
        self.assertEqual(record['Trade Date'], datetime(2013,9,9))



    def verify_record1(self, record):
        self.assertEqual(len(record), 27)
        self.assertEqual(record['RecordType'], 'Buy')
        self.assertEqual(record['KeyValue'], '12734_2010-12-15_Buy_US55608KAB17_HTM_26686800000')
        self.assertEqual(record['Portfolio'], '12734')
        self.assertEqual(record['LocationAccount'], 'BOCHK')
        self.assertEqual(record['Investment'], 'US55608KAB17 HTM')
        self.assertEqual(record['SettleDate'], '2010-12-20')
        self.assertEqual(record['Quantity'], 2700000)
        self.assertAlmostEqual(record['Price'], 98.84)
        self.assertAlmostEqual(record['CounterTDateFx'], 0.1282)
        self.assertEqual(record['CounterFXDenomination'], 'HKD')
        self.assertEqual(record['CounterInvestment'], 'USD')



    def verify_record2(self, record):
        self.assertEqual(len(record), 27)
        self.assertEqual(record['RecordType'], 'Buy')
        self.assertEqual(record['KeyValue'], '12734_2010-12-15_Buy_XS0571508588_HTM_2250000000000')
        self.assertEqual(record['Portfolio'], '12734')
        self.assertEqual(record['LocationAccount'], 'BOCHK')
        self.assertEqual(record['Investment'], 'XS0571508588 HTM')
        self.assertEqual(record['SettleDate'], '2010-12-23')
        self.assertEqual(record['Quantity'], 225000000)
        self.assertAlmostEqual(record['Price'], 100)
        self.assertAlmostEqual(record['CounterTDateFx'], 0.8718)
        self.assertEqual(record['CounterFXDenomination'], 'HKD')
        self.assertEqual(record['CounterInvestment'], 'CNY')



    def verify_record3(self, record):
        self.assertEqual(len(record), 27)
        self.assertEqual(record['RecordType'], 'Buy')
        self.assertEqual(record['KeyValue'], '12734_2010-12-15_Buy_XS0556302163_HTM_26897400000')
        self.assertEqual(record['Portfolio'], '12734')
        self.assertEqual(record['LocationAccount'], 'BOCHK')
        self.assertEqual(record['Investment'], 'XS0556302163 HTM')
        self.assertEqual(record['SettleDate'], '2010-12-21')
        self.assertEqual(record['Quantity'], 2700000)
        self.assertAlmostEqual(record['Price'], 99.62)
        self.assertAlmostEqual(record['CounterTDateFx'], 0.1282)
        self.assertEqual(record['CounterFXDenomination'], 'HKD')
        self.assertEqual(record['CounterInvestment'], 'USD')
