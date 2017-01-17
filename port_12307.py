# coding=utf-8
# 
# Open trade files of portfolio 12307 and convert them to a single file in a
# format required by Advent Geneva system for quick import.
# 

from trade_converter.utility import logger, get_datemode, get_record_fields, \
									get_current_path, convert_datetime_to_string, \
									is_blank_line, is_empty_cell
from xlrd import open_workbook
from xlrd.xldate import xldate_as_datetime



class UnknownBrokerCode(Exception):
	pass

class DuplicateKeys(Exception):
	pass

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
	fix_duplicate_key_value(records)

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
	
	# if trade_info['Acct#'] != '12307':
	# 	logger.error('validate_trade_info(): invalid portfolio code: {0}'.format(trade_info['Acct#']))
	# 	raise InvalidTradeInfo

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



def fix_duplicate_key_value(records):
	"""
	Detect whether there are duplicate keyvalues for different records,
	if there are, modify the keyvalues to make all keys unique.
	"""
	keys = []
	for record in records:
		i = 1
		temp_key = record['KeyValue']
		while temp_key in keys:
			temp_key = record['KeyValue'] + '_' + str(i)
			i = i + 1

		record['KeyValue'] = temp_key
		record['UserTranId1'] = temp_key
		keys.append(record['KeyValue'])

	# check again
	keys = []
	for record in records:
		if record['KeyValue'] in keys:
			logger.error('fix_duplicate_key_value(): duplicate keys still exists, key={0}, investment={1}'.
							format(record['KeyValue'], record['Investment']))
			raise DuplicateKeys()

		keys.append(record['KeyValue'])



def convert_to_geneva_records(output):
	records = []
	record_fields = get_record_fields()
	for trade_info in output:
		records.append(create_record(trade_info, record_fields))

	return records



def map_broker_code(broker_code):
	"""
	Effective 2016-12-13, start using the new broker code.
	"""
	# print(broker_code)
	a_map = {
		'BOCI':'BOCI-EQ',
		'CCBS':'CCB2-EQ',
		'CICC':'CICF-EQ',
		'CITI':'CG-EQ',
		'SBSH':'CG-EQ',		# see 12307 Dec 05 trade file
		'CLSA':'CLSA-EQ',
		'CMSHK':'CMS6-EQ',
		'DBAB':'DBG-EQ',
		'FBCO':'CSFB-EQ',
		'GSCO':'GS-EQ',
		
		# note that for 12307 and other ListCo equity portfolios, since
		# they only do HK equity, so Guo Tai Jun An securities is mapped
		# to its HK arm
		'GUO':'GTHK-EQ',


		'HSCL':'HTIL-EQ',
		'JEFF':'JEF3-EQ',
		'JPM':'JP-EQ',
		'MLCO':'MLAP-EQ',
		'MSCO':'MS-EQ',
		'NOMURA':'INSA-EQ',
		'UBS':'UBSW-EQ',
		'CEBSS':'EBSI-EQ',
		'DAIW':'DAR5-EQ',
		'GFS':'GF01-EQ'
	}

	try:
		return a_map[broker_code]
	except KeyError:
		logger.error('map_broker_code(): broker code {0} does not have a match.'.format(broker_code))
		raise UnknownBrokerCode()



def create_record(trade_info, record_fields):
	# print(trade_info['Trd Dt'])
	known_fields = {
		'RecordAction':'InsertUpdate',
		'KeyValue.KeyName':'UserTranId1',
		'LocationAccount':'JPM',
		'Strategy':'Default',
		'PriceDenomination':'CALC',
		'NetInvestmentAmount':'CALC',
		'NetCounterAmount':'CALC',
		'TradeFX':'',
		'NotionalAmount':'CALC',
		'FundStructure':'CALC',
		'CounterFXDenomination':'USD',
		'CounterTDateFx':'',
		'AccruedInterest':'CALC',
		'InvestmentAccruedInterest':'CALC'
	}
	
	trade_type = {'B':'Buy', 'S':'Sell'}

	new_record = {}
	for record_field in record_fields:

		if record_field in known_fields:
			new_record[record_field] = known_fields[record_field]

		if record_field == 'RecordType':
			new_record[record_field] = trade_type[trade_info['B/S']]
		elif record_field == 'KeyValue':
			new_record[record_field] = create_record_key_value(trade_info)
		elif record_field == 'UserTranId1':
			new_record[record_field] = new_record['KeyValue']
		elif record_field == 'Portfolio':
			new_record[record_field] = trade_info['Acct#']
		elif record_field == 'Investment':
			new_record[record_field] = get_geneva_investment_id(trade_info)[1]
		elif record_field == 'Broker':
			new_record[record_field] = map_broker_code(trade_info['BrkCd'])
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
		elif record_field == 'trade_expenses':
			new_record[record_field] = get_trade_expenses(trade_info)
	# end of for loop

	return new_record



def get_geneva_investment_id(trade_info):
	"""
	As portfolio 12307 is an equity portfolio, the Geneva investment id
	is the Bloomberg ticker without the yellow key, e.g., '11 HK'.

	So assumptions for this function are:

	1. All investment is equity.
	2. In the holdings of the portfolio, the ISIN number to ticker mapping
	is unique.
	"""

	# use a function attribute to store the lookup table, as there is only
	# one instance of a function, all invocations access the same variable.
	# see http://stackoverflow.com/questions/279561/what-is-the-python-equivalent-of-static-variables-inside-a-function
	if 'i_lookup' not in get_geneva_investment_id.__dict__:
		get_geneva_investment_id.i_lookup = {}

	investment_lookup = get_geneva_investment_id.i_lookup
	if len(investment_lookup) == 0:
		lookup_file = get_current_path() + '\\investmentLookup.xls'
		initialize_investment_lookup(investment_lookup, lookup_file)

	# return (name, investment_id)
	logger.debug('get_geneva_investment_id(): trade date {0}'.format(trade_info['Trd Dt']))
	return investment_lookup[trade_info['ISIN']]



def initialize_investment_lookup(investment_lookup, lookup_file):
	"""
	Initialize the lookup table from a file, mapping isin code to investment_id.

	To lookup,

	name, investment_id = investment_lookup(security_id_type, security_id)
	"""
	logger.debug('initialize_investment_lookup(): on file {0}'.format(lookup_file))

	wb = open_workbook(filename=lookup_file)
	ws = wb.sheet_by_name('Sheet1')
	row = 1
	while (row < ws.nrows):
		isin = ws.cell_value(row, 0)
		if isin.strip() == '':
			break

		name = ws.cell_value(row, 1).strip()
		investment_id = ws.cell_value(row, 2).strip()

		investment_lookup[isin] = (name, investment_id)
		row = row + 1



def get_trade_expenses(trade_info):
	"""
	Extract trade related expenses and group them into 5 categories:

	commission, stamp duty, exchange fee, transaction levy, and
	miscellaneous fees.

	Return trade_expenses, as a list of (expense_code, expense_value) tuples.
	"""
	trade_expenses = [('CommissionTradeExpense', trade_info['Commission']), 
						('Stamp_Duty', trade_info['Tax']), 
						('Exchange_Fee', 0), 
						('Transaction_Levy', trade_info['SEC Fee']), 
						('Misc_Fee', trade_info['Fees'])]

	return trade_expenses



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
	return trade_info['Acct#'] + '_' + convert_datetime_to_string(trade_info['Trd Dt']) \
			+ '_' + trade_type[trade_info['B/S']] + '_' + trade_info['ISIN'] \
			+ '_' + str(int(trade_info['Net Setl']*10000)) + '_' + trade_info['BrkCd']



def data_field_begins(ws, row):
	logger.debug('in data_field_begins()')
	
	cell_value = ws.cell_value(row, 0)
	if isinstance(cell_value, str) and cell_value.strip() == 'Acct#':
		return True
	else:
		return False

