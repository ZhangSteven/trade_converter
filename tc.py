# coding=utf-8
# 
# Open trade files of a portfolio and convert them to a single file in a
# format required by Advent Geneva system for quick import.
# 

from trade_converter.utility import logger, get_current_path, get_record_fields
from trade_converter.port_12307 import convert12307



def convert(files, portfolio_id):
	"""
	Read a list of files of the same format, then call the actual converter to
	do the conversion.
	"""
	do_convert = get_converter(portfolio_id)
	output = do_convert(files)
	write_csv(output, portfolio_id)



def get_converter(portfolio_id):
	func_map = {'12307':convert12307}
	return func_map[portfolio_id]



def test_func():
	pass	

def write_csv(output, portfolio_id):
	logger.debug('write_csv(): for portfolio {0}'.format(portfolio_id))

	row = get_record_fields()
	row = row[:-1] + ['TradeExpenses.ExpenseNumber', 'TradeExpenses.ExpenseCode',
				'TradeExpenses.ExpenseAmt']



if __name__ == '__main__':
	convert('haha', '12307')