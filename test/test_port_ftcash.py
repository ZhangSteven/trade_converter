"""
Test the port_ftcsa.py
"""

import unittest2
from datetime import datetime
from xlrd import open_workbook
from trade_converter.utility import get_current_path
from trade_converter.port_ftcsa import read_match_status, read_transaction_file, \
                                        filter_matched_transaction, verify_records, \
                                        convert_to_geneva_records
from trade_converter.port_12307 import fix_duplicate_key_value



class TestFTCash(unittest2.TestCase):

    def __init__(self, *args, **kwargs):
        super(TestFTCash, self).__init__(*args, **kwargs)


    def test_fx_pair(self):
        match_file = get_current_path() + '\\samples\\12229 match results 0118 morning.xlsx'
        transaction_file = get_current_path() + '\\samples\\transactions 12229 no initial pos.xls'
        match_status = read_match_status(match_file)
        isin_list = [entry[2] for entry in match_status]
        transaction_list = []
        read_transaction_file(transaction_file, isin_list, transaction_list)
        matched_transaction_list, bad_isin_list = filter_matched_transaction(transaction_list, match_status)
        records = convert_to_geneva_records(matched_transaction_list)
        fix_duplicate_key_value(records)
        try:
            verify_records(match_status, records, bad_isin_list)
        except:
            self.fail('verify records function failed')

        # from a CSA transaction
        self.verify_record1(self.find_record(records, 'USG46715AB73 HTM', 'Buy', 3750000))
        
        # from a CSW transaction
        self.verify_record2(self.find_record(records, 'USG46715AC56 HTM', 'Sell', 4500000))
        
        # from a CALLED transaction
        self.verify_record3(self.find_record(records, 'US06406JET88 HTM', 'Sell', 100000))

        # from a TNDRL transaction
        self.verify_record4(self.find_record(records, 'USY97279AB28 HTM', 'Sell', 10900000))

        # from a IATSW transaction
        self.verify_record5(self.find_record(records, 'FR0013101599 HTM', 'Sell', 17200000))



    def test_ftcsa2(self):
        match_file = get_current_path() + '\\samples\\12366 match results 0118 morning.xlsx'
        transaction_file = get_current_path() + '\\samples\\transactions 12366 no initial pos.xls'
        match_status = read_match_status(match_file)
        isin_list = [entry[2] for entry in match_status]
        transaction_list = []
        read_transaction_file(transaction_file, isin_list, transaction_list)
        # print(len(transaction_list))
        matched_transaction_list, bad_isin_list = filter_matched_transaction(transaction_list, match_status)
        records = convert_to_geneva_records(matched_transaction_list)
        fix_duplicate_key_value(records)
        try:
            verify_records(match_status, records, bad_isin_list)
        except:
            self.fail('verify records function failed')

        # from a IATSA transaction
        self.verify_record6(self.find_record(records, 'FR0013101599 HTM', 'Buy', 28000000))
 


    def find_record(self, records, investment_id, r_type, quantity):
        for record in records:
            if record['Investment'] == investment_id \
                and record['RecordType'] == r_type \
                and record['Quantity'] == quantity:

                return record

        return None



    def verify_record1(self, record):
        self.assertEqual(len(record), 27)
        self.assertEqual(record['KeyValue'], '12229_2009-12-29_CSA_Buy_USG46715AB73_HTM_299479189900')
        self.assertEqual(record['Portfolio'], '12229')
        self.assertEqual(record['LocationAccount'], 'BOCHK')
        self.assertEqual(record['SettleDate'], '2009-12-29')
        self.assertAlmostEqual(record['Price'], 102.94033333)
        self.assertAlmostEqual(record['CounterTDateFx'], 0.12889919)
        self.assertEqual(record['CounterFXDenomination'], 'HKD')
        self.assertEqual(record['CounterInvestment'], 'USD')



    def verify_record2(self, record):
        self.assertEqual(len(record), 27)
        self.assertEqual(record['RecordType'], 'Sell')
        self.assertEqual(record['KeyValue'], '12229_2010-5-28_CSW_Sell_USG46715AC56_HTM_396011555900')
        self.assertEqual(record['Portfolio'], '12229')
        self.assertEqual(record['LocationAccount'], 'BOCHK')
        self.assertEqual(record['Investment'], 'USG46715AC56 HTM')
        self.assertEqual(record['SettleDate'], '2010-5-28')
        self.assertEqual(record['Quantity'], 4500000)
        self.assertAlmostEqual(record['Price'], 113.0063504)
        self.assertAlmostEqual(record['CounterTDateFx'], 0.12841256)
        self.assertEqual(record['CounterFXDenomination'], 'HKD')
        self.assertEqual(record['CounterInvestment'], 'USD')


    def verify_record3(self, record):
        self.assertEqual(len(record), 27)
        self.assertEqual(record['RecordType'], 'Sell')
        self.assertEqual(record['KeyValue'], '12229_2011-9-15_CALLED_Sell_US06406JET88_HTM_7799500400')
        self.assertEqual(record['Portfolio'], '12229')
        self.assertEqual(record['LocationAccount'], 'BOCHK')
        self.assertEqual(record['Investment'], 'US06406JET88 HTM')
        self.assertEqual(record['SettleDate'], '2011-9-15')
        self.assertEqual(record['Quantity'], 100000)
        self.assertAlmostEqual(record['Price'], 99.99999966)
        self.assertAlmostEqual(record['CounterTDateFx'], 0.12821334)
        self.assertEqual(record['CounterFXDenomination'], 'HKD')
        self.assertEqual(record['CounterInvestment'], 'USD')


    def verify_record4(self, record):
        self.assertEqual(len(record), 27)
        self.assertEqual(record['RecordType'], 'Sell')
        self.assertEqual(record['KeyValue'], '12229_2016-6-10_TNDRL_Sell_USY97279AB28_HTM_786747804800')
        self.assertEqual(record['Portfolio'], '12229')
        self.assertEqual(record['LocationAccount'], 'BOCHK')
        self.assertEqual(record['Investment'], 'USY97279AB28 HTM')
        self.assertEqual(record['SettleDate'], '2016-6-10')
        self.assertEqual(record['Quantity'], 10900000)
        self.assertAlmostEqual(record['Price'], 93)
        self.assertAlmostEqual(record['CounterTDateFx'], 0.12884688)
        self.assertEqual(record['CounterFXDenomination'], 'HKD')
        self.assertEqual(record['CounterInvestment'], 'USD')


    def verify_record5(self, record):
        self.assertEqual(len(record), 27)
        self.assertEqual(record['RecordType'], 'Sell')
        self.assertEqual(record['KeyValue'], '12229_2016-2-25_IATSW_Sell_FR0013101599_HTM_1317294117700')
        self.assertEqual(record['Portfolio'], '12229')
        self.assertEqual(record['LocationAccount'], 'BOCHK')
        self.assertEqual(record['Investment'], 'FR0013101599 HTM')
        self.assertEqual(record['SettleDate'], '2016-2-25')
        self.assertEqual(record['Quantity'], 17200000)
        self.assertAlmostEqual(record['Price'], 98.5711965)
        self.assertAlmostEqual(record['CounterTDateFx'], 0.12870509)
        self.assertEqual(record['CounterFXDenomination'], 'HKD')
        self.assertEqual(record['CounterInvestment'], 'USD')



    def verify_record6(self, record):
        self.assertEqual(len(record), 27)
        self.assertEqual(record['RecordType'], 'Buy')
        self.assertEqual(record['KeyValue'], '12366_2016-1-28_IATSA_Buy_FR0013101599_HTM_2144184780700')
        self.assertEqual(record['Portfolio'], '12366')
        self.assertEqual(record['LocationAccount'], 'BOCHK')
        self.assertEqual(record['Investment'], 'FR0013101599 HTM')
        self.assertEqual(record['SettleDate'], '2016-1-28')
        self.assertEqual(record['Quantity'], 28000000)
        self.assertAlmostEqual(record['Price'], 98.233)
        self.assertAlmostEqual(record['CounterTDateFx'], 0.12827831)
        self.assertEqual(record['CounterFXDenomination'], 'HKD')
        self.assertEqual(record['CounterInvestment'], 'USD')