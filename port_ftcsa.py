# coding=utf-8
# 
# Copied from port_ft.py, the difference is that this program only looks for
# the following types of transactions:
#
# 1. CSA: transferred in (from accounts not under FT)
# 2. CSW: transferred out (to accounts not under FT)
# 3. IATSW: transferred out (internal accounts)
# 4. IATSA: transferred in (internal accounts)
# 5. CALLED: called by issuer 
# 6. TNDRL: buy back by issuer
# 
# Note that we do the above lookup for the list of unmatched positions, i.e.,
# positions that have the above transactions.
#
from trade_converter.utility import logger, get_datemode, get_record_fields, \
									get_current_path, convert_datetime_to_string, \
									is_blank_line, is_empty_cell, get_input_directory
from trade_converter.port_12307 import fix_duplicate_key_value
from trade_converter.tc import write_csv
from xlrd import open_workbook
from xlrd.xldate import xldate_as_datetime
from datetime import datetime
from investment_lookup.id_lookup import get_investment_Ids, \
										get_portfolio_accounting_treatment
import csv, argparse, os



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

class ISINCodeNotFound(Exception):
	pass

class InvalidMatchStatusLine(Exception):
	pass

class TradePriceNotFound(Exception):
	pass

class RecordVerificationFailed(Exception):
	pass



# def convert_ftcsa(files):
# 	"""
# 	Convert the trade files from FT to Geneva format for quick trade
# 	import.

# 	files: a list of trade files.
# 	"""
# 	logger.debug('in convert_ft()')

# 	output = []
# 	for f in files:
# 		read_transaction_file(f, output)

# 	create_geneva_flat_file(output)

# 	records = convert_to_geneva_records(output)
# 	fix_duplicate_key_value(records)

# 	return records



def read_match_status(match_file):
	"""
	Read the match status file, create the list of unmatched positions, in
	the following format:

	(<portfolio_code>, <geneva_investment_id>, <isin>, <difference>)

	isin refers to the isin code of the position, where

	difference = geneva position - bank position
	"""
	wb = open_workbook(filename=match_file)
	ws = wb.sheet_by_index(0)

	fields = read_data_fields(ws, 0)
	row = 1
	output = []
	while row < ws.nrows:
		if is_blank_line(ws, row):
			break
		
		try:
			entry = read_match_line(ws, row, fields)
			if entry != None:
				output.append(entry)
		except:
			pass	# ignore

		row = row + 1

	return output



def read_match_line(ws, row, fields):
	"""
	Extract the following from the line and create the tuple:

	[<portfolio_code>, <geneva_investment_id>, <isin>, <difference>]
	
	"""
	column = 0
	result = ['', '', '', 0]
	for fld in fields:
		if fld == 'Status':
			match_status = ws.cell_value(row, column).strip()
		elif fld == 'Source':
			source = ws.cell_value(row, column).strip()
		elif fld == 'Portfolio':
			result[0] = ws.cell_value(row, column).strip()
		elif fld == 'Investment':
			result[1] = ws.cell_value(row, column).strip()
			if result[1][-4:] == ' HTM' and len(result[1]) == 16:
				result[2] = result[1][:-4]
			else:
				print('investment {0} does not have ISIN code'.format(result[1]))
				raise ISINCodeNotFound()
		elif fld == 'Quantity':
			quantity = ws.cell_value(row, column)
		elif fld == 'Quantity_Diffs':
			quantity_diff = ws.cell_value(row, column)

		column = column + 1
	# end of for loop

	if match_status == 'Near' and source == 'Trustee Geneva':
		result[3] = quantity_diff
	elif match_status == 'Near' and source == 'Trustee Position':
		return None
	elif match_status == 'Unmatched' and source == 'Trustee Geneva':
		result[3] = quantity
	elif match_status == 'Unmatched' and source == 'Trustee Position':
		result[3] = -1 * quantity
	else:
		print('something goes wrong in read match status line')
		raise InvalidMatchStatusLine()

	return result



def read_transaction_file(trade_file, isin_list, output):
	"""
	Note: Read the transaction file from FT, for securities in isin_list only.
	"""
	logger.debug('read_transaction_file(): {0}'.format(trade_file))

	wb = open_workbook(filename=trade_file)
	ws = wb.sheet_by_index(0)

	fields = read_data_fields(ws, 0)
	
	row = 1
	while row < ws.nrows:
		if is_blank_line(ws, row):
			break

		trade_info = read_line(ws, row, fields)
		if not trade_info is None and trade_info['SCTYID_ISIN'] in isin_list:
			# validate_trade_info(trade_info)
			output.append(trade_info)

		row = row + 1
	# end of while loop



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
	Read a line, store as trade information. Note, it only read lines whose
	transaction type is one of the following:

	1. CSA: transferred in (from accounts not under FT)
	2. CSW: transferred out (to accounts not under FT)
	3. IATSW: transferred out (internal accounts)
	4. IATSA: transferred in (internal accounts)
	5. CALLED: called by issuer 
	6. TNDRL: buy back by issuer

	If not, then it returns None.
	"""
	trade_info = {}
	column = 0

	for fld in fields:
		logger.debug('read_line(): row={0}, column={1}'.format(row, column))

		cell_value = ws.cell_value(row, column)
		if isinstance(cell_value, str):
			cell_value = cell_value.strip()

		if fld == 'ACCT_ACNO':
			cell_value = str(int(cell_value))

		if fld in ['SCTYID_SMSEQ', 'SCTYID_SEDOL', 'SCTYID_CUSIP'] and isinstance(cell_value, float):
			cell_value = str(int(cell_value))
		
		if fld in ['TRDDATE', 'STLDATE', 'ENTRDATE']:
			# some FT files uses traditional excel date, some uses
			# a float number to represent date.
			if is_htm_portfolio(trade_info['ACCT_ACNO']):
				cell_value = xldate_as_datetime(cell_value, get_datemode())
			else:
				cell_value = convert_float_to_datetime(cell_value)

		if fld in ['QTY', 'GROSSBAS', 'PRINB', 'RGLBVBAS', 'RGLCCYCLS', \
					'ACCRBAS', 'TRNBVBAS', 'GROSSLCL', 'FXRATE', 'TRADEPRC'] \
					and isinstance(cell_value, str) and cell_value.strip() == '':	
			cell_value = 0.0
		

		check_field_type(fld, cell_value)
		trade_info[fld] = cell_value
		column = column + 1

		try:
			if not trade_info['TRANTYP'] in ['IATSW', 'IATSA', 'CSA', 'CSW', \
				'CALLED', 'TNDRL']:
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
	if fld in ['ACCT_ACNO', 'TRANTYP', 'TRANCOD', 'LCLCCY', 'SCTYID_ISIN'] \
		and not isinstance(cell_value, str):
		logger.error('check_field_type(): field {0} should be string, value={1}'.
						format(fld, cell_value))
		raise InvalidFieldValue()

	if fld in ['QTY', 'GROSSBAS', 'PRINB', 'RGLBVBAS', 'RGLCCYCLS', 'ACCRBAS', \
				'TRNBVBAS', 'GROSSLCL', 'FXRATE', 'TRADEPRC'] \
				and not isinstance(cell_value, float):		
		logger.error('check_field_type(): field {0} should be float, value={1}'.
							format(fld, cell_value))
		raise InvalidFieldValue()

	if fld in ['TRDDATE', 'STLDATE', 'ENTRDATE'] and not isinstance(cell_value, datetime):
		logger.error('check_field_type(): field {0} should be datetime, value={1}'.
							format(fld, cell_value))
		raise InvalidFieldValue()



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
	if diff > 0.01:
		logger.error('validate_trade_info(): FX validation failed, diff={0}'.format(diff))
		raise InvalidTradeInfo()


	if trade_info['TRANTYP'] in ['Purch', 'Sale']:
		# for equity trade
		diff2 = abs(trade_info['PRINB']*trade_info['FXRATE']) - trade_info['QTY']*trade_info['TRADEPRC']
		
		# for bond trade
		diff3 = abs(trade_info['PRINB']*trade_info['FXRATE']) - trade_info['QTY']/100*trade_info['TRADEPRC']
	
		# print('diff2={0}, diff3={1}'.format(diff2, diff3))
		if (abs(diff2) > 0.01 and abs(diff3) > 0.01):
			logger.error('validate_trade_info(): price validation failed')
			raise InvalidTradeInfo()



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
	
	trade_type = {'Purch':'Buy',
					'Sale':'Sell',
					'CSA':'Buy',
					'CSW':'Sell',
					'IATSA':'Buy',
					'IATSW':'Sell',
					'CALLED':'Sell',
					'TNDRL':'Sell'}

	new_record = {}
	for record_field in record_fields:

		if record_field in known_fields:
			new_record[record_field] = known_fields[record_field]

		if record_field == 'RecordType':
			new_record[record_field] = trade_type[trade_info['TRANTYP']]
		elif record_field == 'Portfolio':
			new_record[record_field] = trade_info['ACCT_ACNO']
		elif record_field == 'LocationAccount':
			new_record[record_field] = get_LocationAccount(trade_info['ACCT_ACNO'])
		elif record_field == 'Investment':
			new_record[record_field] = get_geneva_investment_id(trade_info)
		elif record_field == 'EventDate':
			new_record[record_field] = convert_datetime_to_string(trade_info['TRDDATE'])
		elif record_field == 'SettleDate':
			new_record[record_field] = convert_datetime_to_string(trade_info['STLDATE'])
		elif record_field == 'ActualSettleDate':
			new_record[record_field] = new_record['SettleDate']
		elif record_field == 'Quantity':
			new_record[record_field] = trade_info['QTY']
		elif record_field == 'Price':
			new_record[record_field] = get_trade_price(trade_info)
		elif record_field == 'CounterInvestment':
			new_record[record_field] = trade_info['LCLCCY']
		elif record_field == 'CounterFXDenomination':
			new_record[record_field] = get_portfolio_currency(trade_info['ACCT_ACNO'])
		elif record_field == 'CounterTDateFx':
			new_record[record_field] = get_CounterTDateFx(trade_info['ACCT_ACNO'], trade_info['FXRATE'])
		elif record_field == 'trade_expenses':
			new_record[record_field] = get_trade_expenses(trade_info)
	# end of for loop

	if trade_info['TRANTYP'] in ['IATSW', 'CSW']:
		net_amount = trade_info['TRNBVBAS']
	else:
		net_amount = trade_info['PRINB']
	create_record_key_value(new_record, net_amount, trade_info['TRANTYP'])

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



def get_trade_price(trade_info):
	"""
	Only works for purchase/sale, transfers, calls, tender offer.

	If it is transfer, we assume it is always a bond, because only
	the HTM bond portfolios have transfers.
	"""

	if trade_info['TRANTYP'] in ['Purch', 'Sale']:
		return trade_info['TRADEPRC']
	elif trade_info['TRADEPRC'] > 0:
		return trade_info['TRADEPRC']	# use it if it exists
	elif trade_info['TRANTYP'] in ['CSA', 'IATSA', 'CALLED', 'TNDRL']:
		return abs(trade_info['PRINB']*trade_info['FXRATE']/trade_info['QTY']*100)
	elif trade_info['TRANTYP'] in ['IATSW', 'CSW']:
		return abs(trade_info['TRNBVBAS']*trade_info['FXRATE']/trade_info['QTY']*100)
	else:
		logger.error('get_trade_price(): {0} not handled'.format(trade_info['TRANTYP']))
		raise TradePriceNotFound()



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



def create_record_key_value(record, net_amount, prefix):
	"""
	Geneva needs to have a unique key value associated with each record,
	so that different records won't overwrite each other, but the same
	record with different values will update itself.

	That means if we run the function over the same trade input file
	multiple times, a trade record must always be associated with the same
	key value.

	In this case the key value will be a string of the following format:

	<portfolio_code>_<trade_date>_<prefix>_<Buy or Sell>_<hash value of (isin, net_settlement, broker)>
	"""
	record['KeyValue'] = record['Portfolio']+ '_' + record['EventDate'] \
							+ '_' + prefix + '_' + record['RecordType'] \
							+ '_' + convert_investment_id(record['Investment']) \
							+ str(int(abs(net_amount*10000)))

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



def create_geneva_flat_file(output):
	"""
	Extract the ISIN code for each trade, create a Geneva flat file
	to load security master.
	
	The flat file consists of one entry per line, as follows:

	941,Ticker,HK,Equity;
	USY39656AA40,Isin,,;

	For HTM bond, upload the file to \\clfhkgvapp01\FlatFileHTM

	For others (equity and AFS bond), upload the file to 
	\\clfhkgvapp01\FlatFile
	"""
	isin_list = []
	for trade_info in output:
		if trade_info['SCTYID_ISIN'] in isin_list:
			continue
		elif trade_info['SCTYID_ISIN'].strip() == '':
			print('empty isin code!!')
			import sys
			sys.exit()
		else:
			isin_list.append(trade_info['SCTYID_ISIN'])


	with open(get_input_directory()+'\\bondmaster.csv', 'w', newline='') as csvfile:
		file_writer = csv.writer(csvfile)
		
		for isin in isin_list:
			file_writer.writerow([isin, 'Isin', '', ';'])



def filter_transaction_by_isin(isin, transaction_list):
	output = []
	for transaction in transaction_list:
		if transaction['SCTYID_ISIN'] == isin:
			output.append(transaction)

	return output



def filter_record_by_isin(isin, record_list):
	"""
	Note: only works for HTM portfolios.
	"""
	output = []
	for record in record_list:
		if record['Investment'] == isin + ' HTM':
			output.append(record)

	return output



def filter_matched_transaction(transaction_list, match_status):
	"""
	Return the set of transactions that can explain the difference in the
	match status.
	"""
	bad_isin_list = []
	for entry in match_status:
		quantity = 0
		for transaction in filter_transaction_by_isin(entry[2], transaction_list):
			if transaction['TRANTYP'] in ['CSA', 'IATSA']:
				quantity = quantity - transaction['QTY']
			elif transaction['TRANTYP'] in ['CSW', 'IATSW', 'CALLED', 'TNDRL']:
				quantity = quantity + transaction['QTY']
			else:
				print('unhandled transaction type {0}'.format(transaction['TRANTYP']))

		if entry[3] != quantity:
			print('quantity not matched for {0}: {1}, {2}'.
					format(entry[2], entry[3], quantity))
			bad_isin_list.append(entry[2])

	matched_transaction_list = []
	for transaction in transaction_list:
		if not transaction['SCTYID_ISIN'] in bad_isin_list:
			matched_transaction_list.append(transaction)

	return matched_transaction_list, bad_isin_list



def verify_records(match_status, records, bad_isin_list):
	for entry in match_status:
		if entry[2] in bad_isin_list:
			continue

		quantity = 0
		for record in filter_record_by_isin(entry[2], records):
			if record['RecordType'] == 'Buy':
				quantity = quantity - record['Quantity']
			elif record['RecordType'] == 'Sell':
				quantity = quantity + record['Quantity']
			else:
				print('unhandled record type {0}'.format(record['RecordType']))

		if entry[3] != quantity:
			print('quantity not matched for {0}: {1}, {2}'.
					format(entry[2], entry[3], quantity))
			raise RecordVerificationFailed()



def generate_match_records(match_file, transaction_file):
	"""
	From the match status file and the transaction file, create the list of
	records that fix the unmatched positions.
	"""
	match_status = read_match_status(match_file)
	# print('{0} match status read'.format(len(match_status)))
	# print('\n++++++++++++++++\n')
	# for entry in match_status:
	# 	print(entry)

	isin_list = [entry[2] for entry in match_status]
	transaction_list = []
	read_transaction_file(transaction_file, isin_list, transaction_list)
	matched_transaction_list, bad_isin_list = filter_matched_transaction(transaction_list, match_status)
	records = convert_to_geneva_records(matched_transaction_list)
	fix_duplicate_key_value(records)
	print('{0} records generated'.format(len(records)))
	verify_records(match_status, records, bad_isin_list)
	return records




if __name__ == '__main__':
	"""
	Read the match status file (Geneva export of review recon status), and
	the transaction file, then extract the below transactions that can explain
	the difference in the position break report. Note that the match status
	does not contain 'Approved' status, only 'Near' or 'Unmatched'.

	1. CSA: transferred in (from accounts not under FT)
	2. CSW: transferred out (to accounts not under FT)
	3. IATSW: transferred out (internal accounts)
	4. IATSA: transferred in (internal accounts)
	5. CALLED: called by issuer 
	6. TNDRL: buy back by issuer

	If a position break has a difference of say, 100K, but the above transactions
	found in the transaction file does not explain the difference, then they
	are not extracted at all.
	"""
	# Do it over the command line
	# parser = argparse.ArgumentParser(description='Read portfolio trades and create a Geneva trade upload file. Check the config file for path to trade files.')
	# parser.add_argument('match_file')
	# parser.add_argument('transaction_file')
	# args = parser.parse_args()

	# match_file = os.path.join(get_input_directory(), args.match_file)
	# if not os.path.exists(match_file):
	# 	print('{0} does not exist'.format(match_file))
	# 	sys.exit(1)

	# transaction_file = os.path.join(get_input_directory(), args.transaction_file)
	# if not os.path.exists(transaction_file):
	# 	print('{0} does not exist'.format(transaction_file))
	# 	sys.exit(1)

	# generate_match_records(match_file, transaction_file)



	# Instead of getting from the command line, now read a list of position 
	# break reports/transaction files from some where.
	portfolios = ['12229', '12366', '12528', '12548', '12630', '12732', '12733']
	records = []

	for portfolio in portfolios:
		match_file = os.path.join(get_input_directory(), '{0} match results 0118 morning.xlsx'.format(portfolio))
		transaction_file = os.path.join(get_input_directory(), 'transactions {0} no initial pos.xls'.format(portfolio))
		records = records + generate_match_records(match_file, transaction_file)

	print('{0} records'.format(len(records)))
	write_csv(os.path.join(get_input_directory(), 'csa_upload.csv'), records)
