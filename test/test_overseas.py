"""
Test the open_jpm.py
"""

import unittest2
from datetime import datetime
from xlrd import open_workbook
from trade_converter.utility import get_current_path
from trade_converter.port_overseas_bond import read_trade_file, data_field_begins, \
                                                read_data_fields


class TestPortOverseas(unittest2.TestCase):

    def __init__(self, *args, **kwargs):
        super(TestPortOverseas, self).__init__(*args, **kwargs)

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
        ws = wb.sheet_by_name('12528_buy')
        return ws



    def test_read_data_fields(self):
        filename = '\\samples\\sample_overseas.xlsx'
        ws = self.get_worksheet(filename)
        row = 0
        while not data_field_begins(ws, row):
            row = row + 1

        self.assertEqual(row, 5)
        fields = read_data_fields(ws, row)
        self.assertEqual(len(fields), 25)
        