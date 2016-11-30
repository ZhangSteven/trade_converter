# coding=utf-8
# 
# Open trade files of portfolio 12307 and convert them to a single file in a
# format required by Advent Geneva system for quick import.
# 

from utility import logger, get_datemode
from xlrd import open_workbook
from xlrd.xldate import xldate_as_datetime
from tc import get_record_fields



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

	records = convert_to_geneva_records(output)
	detect_duplicate_key_value(records)

	return records



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



def detect_duplicate_key_value(records):
	pass



def convert_to_geneva_records(output):
	records = []
	record_fields = get_record_fields()
	for trade_info in output:
		records.append(create_record(trade_info, fields))



def create_record(trade_info, record_fields):

	known_fields = {
		'RecordAction':'InsertUpdate',
		'KeyValue.KeyName':'UserTranId1',
		'LocationAccount':'JPM',
		'Strategy':'Default',
		'PriceDenomination':'CALC',
		'NetInvestmentAmount','CALC',
		'NetCounterAmount','CALC',
		'TradeFX','',
		'NotionalAmount','CALC',
		'FundStructure','CALC',
		'CounterFXDenomination','USD',
		'AccruedInterest ','CALC',
		'InvestmentAccruedInterest ','CALC'
	}
	
	new_record = {}
	for record_field in record_fields:

		if record_field in known_fields:
			new_record[record_field] = known_fields[record_field]

		if record_field == 'RecordType':
			if trade_info['B/S'] == 'B':
				new_record[record_field] = 'Buy'
			else:
				new_record[record_field] = 'Sell'

		elif record_field == 'KeyValue':
			new_record[record_field] = create_record_key_value(trade_info)
		elif record_field == 'UserTranId1':
			new_record[record_field] = new_record['KeyValue']
		elif record_field == 'Portfolio':
			new_record[record_field] = trade_info['Acct#']
		elif record_field == 'Investment':
			new_record[record_field] = get_geneva_investment_id(trade_info)
		elif record_field == 'Broker':
			new_record[record_field] = trade_info['BrkCd']
		elif record_field == 'EventDate':
			new_record[record_field] = convert_datetime_to_string(trade_info['Trd Dt'])
		elif record_field == 'SettleDate':
			new_record[record_field] = convert_datetime_to_string(trade_info['Setl Dt'])
		elif record_field == 'ActualSettleDate':
			new_record[record_field] = new_record['SettleDate']
		elif record_field == 'Quantity':
			new_record[record_field] = trade_info['Units']
		elif record_field == 'Price':
			new_record[record_field] = trade_info['Unit Price']
		elif record_field == 'CounterInvestment':
			new_record[record_field] = trade_info['Cur']
		elif record_field == 'CounterTDateFx':
			new_record[record_field] = get_trade_day_FX(trade_info['Cur'], trade_info['Trd Dt'])
		elif record_field == 'TradeExpenses':
			new_record[record_field] = get_trade_expenses(trade_info)
	# end of for loop

	return new_record



def create_record_key_value(trade_info):
	"""
	Geneva needs to have a unique key value associated with each record,
	so that different records won't overwrite each other, but the same
	record with different values will update itself.

	That means if we run the function over the same trade input file
	multiple times, a trade record must always be associated with the same
	key value.

	In this case the key value will be a string of the following format:

	<portfolio_code>_<trade_date>_<Buy or Sell>_<hash value of (isin, net_settlement, broker)>
	"""
	trade_type = {'B':'Buy', 'S':'Sell'}
	return trade_info['Acct#'] + '_' + convert_datetime_to_string(trade_info['Trd Dt']) + \
			'_' + trade_type[trade_info['B/S']] + '_' + \
			int_to_string(hash((trade_info['ISIN'], trade_info['Net Setl'], trade_info['BrkCd'])))



def int_to_string(int_x):
	if int_x < 0:
		return 'n'+str(int_x)
	else:
		return str(int_x)



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
