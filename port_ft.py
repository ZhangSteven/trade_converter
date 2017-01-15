# coding=utf-8
# 
# Open transaction files from franklin templeton and convert them to a single 
# file in a format required by Advent Geneva system for trade import.
# 
# Note that FT transactions file does NOT have:
#
#	1. Broker information: all broker information will be put as "journal_entry".
#	2. Detailed breakdown of fees: we can only calculate a total fee by
#		subtracting the total settlement amount and the price*quantity. So
#		all fees will be put into miscellaneous fees.
#
from trade_converter.utility import logger, get_datemode, get_record_fields, \
									get_current_path, convert_datetime_to_string, \
									is_blank_line, is_empty_cell
from xlrd import open_workbook
from xlrd.xldate import xldate_as_datetime
from datetime import datetime
from investment_lookup.id_lookup import get_investment_Ids, \
										get_portfolio_accounting_treatment



class InvalidFieldValue(Exception):
	pass

class InvalidTradeInfo(Exception):
	pass

class LocationAccountNotFound(Exception):
	pass

class PortfolioCurrencyNotFound(Exception):
	pass

class InvestmentIdNotFound(Exception):
	pass

class TradeExpenseNotHandled(Exception):
	pass



def convert_ft(files):
	"""
	Convert the trade files from FT to Geneva format for quick trade
	import.

	files: a list of trade files.
	"""
	logger.debug('in convert_ft()')

	output = []
	for f in files:
		read_transaction_file(f, output)

	records = convert_to_geneva_records(output)
	fix_duplicate_key_value(records)

	return records



def read_transaction_file(trade_file, output):
	"""
	Note: the transaction file from FT contains all kinds of transactions,
	including purchase/sale, cash movements, position adjustments, paydown,
	bond exchange offer, called by issuer, FX transactions, etc.

	For simplicity, we filtered out purchase/sale first.
	"""
	logger.debug('read_transaction_file(): {0}'.format(trade_file))

	wb = open_workbook(filename=trade_file)
	ws = wb.sheet_by_index(0)

	fields = read_data_fields(ws, 0)
	
	row = 1
	# starting_pos = len(output)
	while not is_blank_line(ws, row):
		trade_info = read_line(ws, row, fields)
		if not trade_info is None:
			validate_trade_info(trade_info)
			output.append(trade_info)
		row = row + 1

	# total_info = read_total(ws, row)
	# validate_total(total_info, fields, output, starting_pos)



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

		check_field_type(fld, cell_value)

		if fld == 'ACCT_ACNO':
			cell_value = str(int(cell_value))

		if fld in ['SCTYID_SMSEQ', 'SCTYID_CUSIP'] and isinstance(cell_value, float):
			cell_value = str(int(cell_value))
		
		if fld in ['TRDDATE', 'STLDATE', 'ENTRDATE']:
			# some FT files uses traditional excel date, some uses
			# a float number to represent date.
			if is_htm_portfolio(trade_info['ACCT_ACNO']):
				cell_value = xldate_as_datetime(cell_value, get_datemode())
			else:
				cell_value = convert_float_to_datetime(cell_value)

		# if fld in ['QTY', 'ACCRBAS', 'TRADEPRC']:
		# 	logger.debug('read_line(): read field {0}'.format(fld))
		# 	cell_value = read_value_as_float(cell_value)

		trade_info[fld] = cell_value
		column = column + 1

		try:
			if not trade_info['TRANTYP'] in ['Purch', 'Sale']:
				trade_info = None
				break
		except KeyError:
			pass
	# end of for loop

	return trade_info



def is_htm_portfolio(portfolio_id):
	# htm_portfolio = ['12229', '12366', '12528', '12548', '12630', '12732', '12733']
	# if portfolio_id in htm_portfolio:
	# 	return True
	# else:
	# 	return False

	if get_portfolio_accounting_treatment(portfolio_id) == 'HTM':
		return True
	else:
		return False




def check_field_type(fld, cell_value):
	if fld in ['TRANTYP', 'TRANCOD', 'LCLCCY', 'SCTYID_SEDOL', 'SCTYID_ISIN'] \
		and not isinstance(cell_value, str):
		logger.error('check_field_type(): field {0} should be string, value={1}'.
						format(fld, cell_value))
		raise InvalidFieldValue()

	if fld in ['ACCT_ACNO', 'TRDDATE', 'STLDATE', 'ENTRDATE', 'GROSSBAS', 
				'PRINB', 'GROSSLCL', 'FXRATE'] and not isinstance(cell_value, float):
		logger.error('check_field_type(): field {0} should be float, value={1}'.
							format(fld, cell_value))
		raise InvalidFieldValue()



# def read_value_as_float(cell_value):
# 	if cell_value == '':
# 		return 0
# 	if isinstance(cell_value, float):
# 		return cell_value

# 	logger.error('read_value_as_float(): invalid value={1}'.format(fld, cell_value))
# 	raise InvalidFieldValue()



def convert_float_to_datetime(value):
	"""
	the value is of type float, in the form of 'mmddyyyy' or 'mddyyyy'
	"""
	month = int(value/1000000)
	day = int((value - month*1000000)/10000)
	year = int(value - month*1000000 - day*10000)
	return datetime(year, month, day)



def validate_trade_info(trade_info):
	logger.debug('validate_trade_info(): trade date={0}, isin={1}, gross amount={2}'.
					format(trade_info['TRDDATE'], trade_info['SCTYID_ISIN'], trade_info['GROSSBAS']))

	if trade_info['STLDATE'] < trade_info['TRDDATE'] or \
		trade_info['ENTRDATE'] < trade_info['TRDDATE']:
		logger.error('validate_trade_info(): invalid dates, trade date={0}, settle day={1}, enterday={2}'.
						format(trade_info['TRDDATE'], trade_info['STLDATE'], trade_info['ENTRDATE']))
		raise InvalidTradeInfo()

	diff = abs(trade_info['GROSSBAS'] * trade_info['FXRATE'] - trade_info['GROSSLCL'])
	if diff > 0.001:
		logger.error('validate_trade_info(): FX validation failed')
		raise InvalidTradeInfo()

	if trade_info['TRANTYP'] in ['Purch', 'Sale']:
		if not isinstance(trade_info['QTY'], float) or not isinstance(trade_info['TRADEPRC'], float):
			logger.error('validate_trade_info(): quantity={0}, price={1}, is not of type float'.
							format(trade_info['QTY'], trade_info['TRADEPRC']))
			raise InvalidTradeInfo()

		# for equity trade
		diff2 = abs(trade_info['PRINB']*trade_info['FXRATE']) - trade_info['QTY']*trade_info['TRADEPRC']
		
		# for bond trade
		diff3 = abs(trade_info['PRINB']*trade_info['FXRATE']) - trade_info['QTY']/100*trade_info['TRADEPRC']
		# print('diff2={0}, diff3={1}'.format(diff2, diff3))
		if (abs(diff2) > 0.001 and abs(diff3) > 0.001):
			logger.error('validate_trade_info(): price validation failed')
			raise InvalidTradeInfo()



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



def get_LocationAccount(portfolio_id):
	boc_portfolios = ['12229', '12366', '12528', '12630', '12732', '12733']
	jpm_portfolios = ['12548']

	if portfolio_id in boc_portfolios:
		return 'BOCHK'
	elif portfolio_id in jpm_portfolios:
		return 'JPM'
	else:
		logger.error('get_LocationAccount(): no LocationAccount found for portfolio id {0}'.
						format(portfolio_id))
		raise LocationAccountNotFound()



def get_portfolio_currency(portfolio_id):
	# A portfolio's base currency
	usd_portfolio = ['21815']
	hkd_portfolio = ['12229', '12366', '12528', '12548', '12630', '12732', '12733']

	if portfolio_id in usd_portfolio:
		return 'USD'
	elif portfolio_id in hkd_portfolio:
		return 'HKD'
	else:
		logger.error('get_portfolio_currency(): no portfolio currency found for {0}'.
						format(portfolio_id))
		raise PortfolioCurrencyNotFound()



def get_FT_portfolio_currency(portfolio_id):
	# FT portfolio's base currency setting. It is not always consistent with
	# the correct setting.
	FT_usd_portfolio = ['21815']
	FT_hkd_portfolio = ['12229', '12366', '12528', '12548', '12630', '12732', \
						'12733', '12307', '19437']

	if portfolio_id in FT_usd_portfolio:
		return 'USD'
	elif portfolio_id in FT_hkd_portfolio:
		return 'HKD'
	else:
		logger.error('get_FT_portfolio_currency(): no portfolio currency found for {0}'.
						format(portfolio_id))
		raise PortfolioCurrencyNotFound()



def get_CounterTDateFx(portfolio_id, FT_fx):
	if get_portfolio_currency(portfolio_id) == get_FT_portfolio_currency(portfolio_id):
		return FT_fx
	else:
		return ''



def create_record(trade_info, record_fields):

	known_fields = {
		'RecordAction':'InsertUpdate',
		'KeyValue.KeyName':'UserTranId1',
		'Strategy':'Default',
		'Broker':'journaling entries',
		'PriceDenomination':'CALC',
		'NetInvestmentAmount':'CALC',
		'NetCounterAmount':'CALC',
		'TradeFX':'',
		'NotionalAmount':'CALC',
		'FundStructure':'CALC',
		'AccruedInterest':'CALC',
		'InvestmentAccruedInterest':'CALC'
	}
	
	trade_type = {'Purch':'Buy', 'Sale':'Sell'}

	new_record = {}
	for record_field in record_fields:

		if record_field in known_fields:
			new_record[record_field] = known_fields[record_field]

		if record_field == 'RecordType':
			new_record[record_field] = trade_type[trade_info['TRANTYP']]
		# elif record_field == 'KeyValue':
		# 	new_record[record_field] = create_record_key_value(trade_info)
		# elif record_field == 'UserTranId1':
		# 	new_record[record_field] = new_record['KeyValue']
		elif record_field == 'Portfolio':
			new_record[record_field] = trade_info['ACCT_ACNO']
		elif record_field == 'LocationAccount':
			new_record[record_field] = get_LocationAccount(trade_info['ACCT_ACNO'])
		elif record_field == 'Investment':
			new_record[record_field] = get_geneva_investment_id(trade_info)[1]
		# elif record_field == 'Broker':
		# 	new_record[record_field] = map_broker_code(trade_info['BrkCd'])
		elif record_field == 'EventDate':
			new_record[record_field] = convert_datetime_to_string(trade_info['TRDDATE'])
		elif record_field == 'SettleDate':
			new_record[record_field] = convert_datetime_to_string(trade_info['STLDATE'])
		elif record_field == 'ActualSettleDate':
			new_record[record_field] = new_record['SettleDate']
		elif record_field == 'Quantity':
			new_record[record_field] = trade_info['QTY']
		elif record_field == 'Price':
			new_record[record_field] = trade_info['TRADEPRC']
		elif record_field == 'CounterInvestment':
			new_record[record_field] = trade_info['LCLCCY']
		elif record_field == 'CounterFXDenomination':
			new_record[record_field] = get_portfolio_currency(trade_info['ACCT_ACNO'])
		elif record_field == 'CounterTDateFx':
			new_record[record_field] = get_CounterTDateFx(trade_info['ACCT_ACNO'], trade_info['FXRATE'])
		elif record_field == 'trade_expenses':
			new_record[record_field] = get_trade_expenses(trade_info)
	# end of for loop

	create_record_key_value(new_record, trade_info['PRINB'])

	return new_record



def get_geneva_investment_id(trade_info):
	"""
	Get the Geneva investment ID for a position. 

	The function is not complete yet, now we assume it is only used for
	HTM portfolios only, otherwise it will throw an error.
	"""
	if not is_htm_portfolio(trade_info['ACCT_ACNO']):
		logger.error('get_geneva_investment_id(): not a HTM portfolio')
		raise InvestmentIdNotFound()

	if trade_info['SCTYID_ISIN'] != '':
		return get_investment_Ids(trade_info['ACCT_ACNO'], 'ISIN', trade_info['SCTYID_ISIN'])[0]
	elif trade_info['SCTYID_SEDOL'] != '':
		return get_investment_Ids(trade_info['ACCT_ACNO'], 'SEDOL', trade_info['SCTYID_SEDOL'])[0]
	elif trade_info['SCTYID_CUSIP'] != '':
		return get_investment_Ids(trade_info['ACCT_ACNO'], 'CUSIP', trade_info['SCTYID_CUSIP'])[0]
	else:
		logger.error('get_geneva_investment_id(): no security identifier found for SCTYID_SMSEQ:{0}'.
						format(trade_info['SCTYID_SMSEQ']))
		raise InvestmentIdNotFound()




# def initialize_investment_lookup(investment_lookup, lookup_file):
# 	"""
# 	Initialize the lookup table from a file, mapping isin code to investment_id.

# 	To lookup,

# 	name, investment_id = investment_lookup(security_id_type, security_id)
# 	"""
# 	logger.debug('initialize_investment_lookup(): on file {0}'.format(lookup_file))

# 	wb = open_workbook(filename=lookup_file)
# 	ws = wb.sheet_by_name('Sheet1')
# 	row = 1
# 	while (row < ws.nrows):
# 		isin = ws.cell_value(row, 0)
# 		if isin.strip() == '':
# 			break

# 		name = ws.cell_value(row, 1).strip()
# 		investment_id = ws.cell_value(row, 2).strip()

# 		investment_lookup[isin] = (name, investment_id)
# 		row = row + 1



def get_trade_expenses(trade_info):
	"""
	Extract trade related expenses and group them into 5 categories:

	commission, stamp duty, exchange fee, transaction levy, and
	miscellaneous fees.

	Return trade_expenses, as a list of (expense_code, expense_value) tuples.

	For FT historical trades, equity trade expenses are not handled yet.
	currently we only handle bond trades, there is no trade expense.
	"""
	if not is_htm_portfolio(trade_info['ACCT_ACNO']):
		logger.error('get_trade_expenses(): trade expense not handled')
		raise TradeExpenseNotHandled()

	return []	# no explicit trade expense for bond trade



def create_record_key_value(record, net_amount):
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
	record['KeyValue'] = record['Portfolio']+ '_' + record['EventDate'] + '_' \
							+ record['RecordType'] + '_' + record['Investment'] \
							+ '_' + str(int(net_amount*10000))

	record['UserTranId1'] = record['KeyValue']
