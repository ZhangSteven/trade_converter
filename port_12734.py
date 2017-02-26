# coding=utf-8
# 
# Open transaction files from settlement for bond portfolio 12734 and convert 
# them to Geneva trade upload format.
#
from trade_converter.utility import logger, get_record_fields, \
									get_input_directory, \
									convert_datetime_to_string
from trade_converter.port_12307 import convert_to_geneva_records, \
									fix_duplicate_key_value
from small_program.read_file import read_file
from xlrd.xldate import xldate_as_datetime
from datetime import datetime
import csv



class InvalidaLineInfo(Exception):
	pass

class ISINMapFailure(Exception):
	pass



def convert12734(files):
	"""
	Convert the trade files from settlement to Geneva format for quick trade
	import.

	files: a list of trade files.
	"""
	output_list = []
	error_list = []
	for f in files:
		logger.debug('convert12734(): read file {0}'.format(f))
		read_transaction_file(f, output_list, error_list)

	records = convert_to_geneva_records(output_list)
	fix_duplicate_key_value(records)

	for error_entry in error_list:
		print('trade in error: {0}'.format(error_entry['Trade Date']))

	return records



def read_transaction_file(file, output_list, error_list):
	logger.debug('read_transaction_file(): read file: {0}'.format(file))
	output, row_in_errow = read_file(file, read_line, validate_line, 13)
	output_list.extend(output)
	error_list.extend(row_in_errow)



def validate_line(line_info):
	"""
	Validate the following:

	1. Form serial with trade date (date)

	2. Security code is ISIN
	"""
	if not get_date_from_serial(line_info['Form Serial No.']) == line_info['Trade Date']:
		logger.error('validate_line(): inconsistent date {0}'.
						format(line_info['Trade Date']))
		raise InvalidaLineInfo()

	if not is_valid_isin(line_info['Security Code']):
		logger.error('validate_line(): invalid ISIN {0} on {1}'.
						format(line_info['Security Code'], line_info['Trade Date']))
		raise InvalidaLineInfo()

	if not line_info['Buy/Sell'] in ['Buy', 'Sell']:
		logger.error('validate_line(): invalid Buy/Sell action {0}'.
						format(line_info['Buy/Sell']))
		raise InvalidaLineInfo()



def read_line(ws, row, fields):
	"""
	Read the trade information from a line.
	"""
	line_info = {}
	column = 0

	for fld in fields:
		logger.debug('read_line(): row={0}, column={1}'.format(row, column))

		cell_value = ws.cell_value(row, column)
		if isinstance(cell_value, str):
			cell_value = cell_value.strip()

		if fld == 'Item No.':
			cell_value = int(cell_value)

		if fld == 'Security Code':
			if isinstance(cell_value, float):
				cell_value = str(int(cell_value))
			if not is_valid_isin(cell_value):
				cell_value = map_to_isin(cell_value)

		if fld in ['Trade Date', 'Value Date']:
			cell_value = xldate_as_datetime(cell_value, 0)
		
		line_info[fld] = cell_value
		column = column + 1

	return line_info



def get_date_from_serial(serial_no):
	"""
	If the serial string is 'GFI-10-0630', then date is 2010-6-30.
	"""
	tokens = serial_no.split('-')
	year = int(tokens[1]) + 2000
	month = int(int(tokens[2])/100)
	day = int(tokens[2]) - month*100
	return datetime(year, month, day)



def is_valid_isin(security_code):
	if len(security_code) == 12:
		return True
	else:
		return False



def map_to_isin(security_no):
	"""
	Map the non-ISIN security code to ISIN.
	"""
	isin_map = {
		'BNYHFB12001':'HK0000097490',
		'CMU: HSBCFN13002':'HK0000134780',
		'EI7283738':'HK0000083706',
		'EI8608990':'HK0000091832',
		'EI9135894':'HK0000096856',
		'EJ0975098':'HK0000175916'
	}

	try:
		return isin_map[security_no]
	except KeyError:
		logger.error('map_to_isin(): {0} does not map an ISIN code'.format(security_no))
		raise ISINMapFailure(Exception)



def convert_to_geneva_records(output):
	records = []
	record_fields = get_record_fields()
	for trade_info in output:
		records.append(create_record(trade_info, record_fields))

	return records



def create_record(trade_info, record_fields):
	"""
	1. Brokers are all 'journaling entries'

	2. Key value contains security name.
	"""
	known_fields = {
		'RecordAction':'InsertUpdate',
		'KeyValue.KeyName':'UserTranId1',
		'Strategy':'Default',
		'Broker':'journaling entries',
		'Portfolio':'12734',
		'LocationAccount':'BOCHK',
		'PriceDenomination':'CALC',
		'NetInvestmentAmount':'CALC',
		'NetCounterAmount':'CALC',
		'CounterFXDenomination':'HKD',
		'TradeFX':'',
		'NotionalAmount':'CALC',
		'FundStructure':'CALC',
		'AccruedInterest':'CALC',
		'InvestmentAccruedInterest':'CALC',
		'trade_expenses':[]
	}

	new_record = {}
	for fld in known_fields:
		new_record[fld] = known_fields[fld]

	new_record['RecordType'] = trade_info['Buy/Sell']
	new_record['Investment'] = trade_info['Security Code'] + ' HTM'
	new_record['EventDate'] = convert_datetime_to_string(trade_info['Trade Date'])
	new_record['SettleDate'] = convert_datetime_to_string(trade_info['Value Date'])
	new_record['ActualSettleDate'] = new_record['SettleDate']
	new_record['Quantity'] = trade_info['Par Value']
	new_record['Price'] = trade_info['Price (%)']
	new_record['CounterInvestment'] = convert_currency(trade_info['Currency'])
	new_record['CounterTDateFx'] = get_fxrate(new_record['CounterInvestment'])

	create_record_key_value(new_record, new_record['Quantity']*new_record['Price'])

	return new_record



def convert_currency(currency):
	if currency in ['HKD', 'CNY', 'USD']:
		return currency

	c_map = {
		'US$':'USD',
		'HK$':'HKD'
	}

	return c_map[currency]



def get_fxrate(currency):
	"""
	Note: Here we hardcoded the currency because we don't care about the
	historical FX rate in the trade upload in the current portfolio.
	"""
	if currency == 'HKD':
		return ''
	elif currency == 'USD':
		return 0.1282	# 7.8 HKD = 1 USD
	elif currency == 'CNY':
		return 0.8718	# 6.8 CNY = 1 USD
	else:
		return ''



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
							+ record['RecordType'] + '_' \
							+ convert_investment_id(record['Investment']) \
							+ str(int(abs(net_amount*100)))

	record['UserTranId1'] = record['KeyValue']



def convert_investment_id(investment_id):
	"""
	Geneva investment id may contain spaces, replace the spaces with
	underscore ('_')
	"""
	result = ''
	for token in investment_id.split():
		result = result + token + '_'

	return result
