# coding=utf-8
# 
# Open trade files of a portfolio and convert them to a single file in a
# format required by Advent Geneva system for quick import.
# 

import csv, argparse, glob, os, sys
from trade_converter.utility import logger, get_current_path, get_record_fields, \
									get_input_directory
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



def get_all_trade_files(directory):
	"""
	Get all trade files under a directory. Here we assume all .xls files
	under the directory are trade files. Other files and sub directories
	are ignored.
	"""
	return glob.glob(directory+'\\*.xls')



def write_csv(file, records):
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
	parser = argparse.ArgumentParser(description='Read portfolio trades and create a Geneva trade upload file. Check the config file for path to trade files.')
	parser.add_argument('portfolio_id')
	parser.add_argument('--folder', help='folder containing multiple trade files', required=False)
	parser.add_argument('--file', help='input trade file', required=False)
	args = parser.parse_args()

	if not args.file is None:
		file = get_input_directory() + '\\' + args.file
		if not os.path.exists(file):
			print('{0} does not exist'.format(file))
			sys.exit(1)
		files = [file]
	elif not args.folder is None:
		folder = get_input_directory() + '\\' + args.folder
		if not os.path.exists(folder) or not os.path.isdir(folder):
			print('{0} is not a valid directory'.format(folder))
			sys.exit(1)

		files = get_all_trade_files(folder)
	else:
		print('Please provide either --file or --folder input')
		sys.exit(1)

	do_convert = get_converter(args.portfolio_id)
	records = do_convert(files)

	output_file = get_input_directory() + '\\trade_upload.csv'
	write_csv(output_file, records)