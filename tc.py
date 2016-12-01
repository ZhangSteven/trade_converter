# coding=utf-8
# 
# Open trade files of a portfolio and convert them to a single file in a
# format required by Advent Geneva system for quick import.
# 

import csv
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



def write_csv(file, records):
	logger.debug('write_csv(): for portfolio {0}'.format(portfolio_id))

	with open(file, 'w', newline='') as csvfile:
		logger.debug('write_csv(): {0}'.format(file))
		file_writer = csv.writer(csvfile)

		fields = get_record_fields()
		file_writer.writerow(fields[:-1] + ['TradeExpenses.ExpenseNumber', 'TradeExpenses.ExpenseCode',
					'TradeExpenses.ExpenseAmt'])

		for record in records:
			trade_expenses = record['trade_expenses']
			for expense_number in range(len(trade_expenses)):
				row = []
				for fld in fields:
					if fld == 'trade_expenses':
						row = row + [expense_number+1, trade_expenses[expense_number][0],
										trade_expenses[expense_number][1]]
						break

					if expense_number == 0:
						item = record[fld]
					else:
						item = ''

					row.append(item)

				file_writer.writerow(row)



if __name__ == '__main__':
	portfolio_id = '12307'
	file = get_current_path() + '\\samples\\12307-20161111.xls'
	files = [file]

	do_convert = get_converter(portfolio_id)
	records = do_convert(files)

	output_file = get_current_path() + '\\trades_upload.csv'
	write_csv(output_file, records)