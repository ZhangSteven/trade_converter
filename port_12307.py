# coding=utf-8
# 
# Open trade files of portfolio 12307 and convert them to a single file in a
# format required by Advent Geneva system for quick import.
# 

from utility import logger, get_datemode
from xlrd import open_workbook
from xlrd.xldate import xldate_as_datetime



class InvalidTradeInfo(Exception):
	pass



def convert12307(files):
	"""
	Convert the trade files of portfolio 12307 to Geneva format for quick 
	import.

	files: a list of trade files.
	"""
	logger.debug('in convert12307()')

	output = []
	for f in files:
		read_trade_file(f, output)

	detect_duplicate_trade_no(output)
	return to_standard_output(output)



def read_trade_file(trade_file, output):
	logger.debug('read_trade_file(): {0}'.format(trade_file))

	wb = open_workbook(filename=trade_file)
	ws = wb.sheet_by_index(0)
	row = 0

	while not data_field_begins(ws, row):
		row = row + 1

	fields = read_data_fields(ws, row)
	row = row + 1

	while not is_blank_line(ws, row):
		trade_info = read_line(ws, row, fields)
		validate_trade_info(trade_info)
		output.append(trade_info)
		row = row + 1



def read_data_fields(ws, row):
	column = 0
	fields = []
	while column < ws.ncols:
		cell_value = ws.cell_value(row, column)
		if is_empty_cell(ws, row, column):
			break

		fields.append(cell_value.strip())
		column = column + 1

	return fields



def read_line(ws, row, fields):
	"""
	Read the trade information from a line.
	"""
	trade_info = {}
	column = 0

	for fld in fields:
		logger.debug('read_line(): row={0}, column={1}'.format(row, column))

		cell_value = ws.cell_value(row, column)
		if isinstance(cell_value, str):
			cell_value = cell_value.strip()

		if fld in ['Acct#', 'Trade#'] and isinstance(cell_value, float):
			cell_value = str(int(cell_value))
		elif fld in ['Trd Dt', 'Setl Dt']:
			cell_value = xldate_as_datetime(cell_value, get_datemode())

		trade_info[fld] = cell_value
		column = column + 1
	# end of for loop

	return trade_info



def validate_trade_info(trade_info):
	logger.debug('validate_trade_info(): trade date={0}, isin={1}'.
					format(trade_info['Trd Dt'], trade_info['ISIN']))
	
	if trade_info['Acct#'] != '12307':
		logger.error('validate_trade_info(): invalid portfolio code: {0}'.format(trade_info['Acct#']))
		raise InvalidTradeInfo

	if trade_info['B/S'] == 'B':
		settled_amount = trade_info['Units']*trade_info['Unit Price'] + \
							(trade_info['Commission'] + trade_info['Tax'] + \
							trade_info['Fees'] + trade_info['SEC Fee'])

	elif trade_info['B/S'] == 'S':
		settled_amount = trade_info['Units']*trade_info['Unit Price'] - \
							(trade_info['Commission'] + trade_info['Tax'] + \
							trade_info['Fees'] + trade_info['SEC Fee'])

	else:
		logger.error('validate_trade_info(): invalid trade instruction: {0}'.format(trade_info['B/S']))
		raise InvalidTradeInfo

	if abs(settled_amount - trade_info['Net Setl']) > 0.0001:
		logger.error('validate_trade_info(): net settlement amount does not match, calculated={0}, read={1}'.
						format(settled_amount, trade_info['Net Setl']))
		raise InvalidTradeInfo



def detect_duplicate_trade_no(output):
	pass



def to_standard_output(output):
	pass



def data_field_begins(ws, row):
	logger.debug('in data_field_begins()')
	
	cell_value = ws.cell_value(row, 0)
	if isinstance(cell_value, str) and cell_value.strip() == 'Acct#':
		return True
	else:
		return False



def is_blank_line(ws, row):
	for i in range(5):
		if not is_empty_cell(ws, row, i):
			return False

	return True



def is_empty_cell(ws, row, column):
	cell_value = ws.cell_value(row, column)
	if not isinstance(cell_value, str) or cell_value.strip() != '':
		return False
	else:
		return True
