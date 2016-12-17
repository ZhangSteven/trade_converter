"""
Test the open_jpm.py
"""

import unittest2
from datetime import datetime
from xlrd import open_workbook
from trade_converter.utility import get_current_path
from trade_converter.port_ft import read_data_fields, read_line, \
                                    validate_trade_info, InvalidTradeInfo



class TestPortFTError(unittest2.TestCase):

    def __init__(self, *args, **kwargs):
        super(TestPortFTError, self).__init__(*args, **kwargs)

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



    def test_validate_error(self):
        ws = self.get_worksheet('\\samples\\sample_FT_error.xlsx')
        fields = read_data_fields(ws, 0)
        trade_info = read_line(ws, 1, fields)
        with self.assertRaises(InvalidTradeInfo):
            validate_trade_info(trade_info)



    def test_validate_error2(self):
        ws = self.get_worksheet('\\samples\\sample_FT_error2.xlsx')
        fields = read_data_fields(ws, 0)
        trade_info = read_line(ws, 1, fields)
        with self.assertRaises(InvalidTradeInfo):
            validate_trade_info(trade_info)