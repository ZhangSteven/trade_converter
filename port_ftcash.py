# coding=utf-8
# 
# Copied from port_ftcsa.py, the difference is that this program only looks for
# the following types of transactions:
#
# 1. FXPurch, FXSale: buy one currency and sell another at the same time.
# 	These two transactions always occur in pairs.
# 2. CashAdd: Cash deposit.
# 3. CashWth: Cash withdrawal.
# 4. IATCA, IATCW: cash transfers among accounts under FT control.
# 	These two transactions always occur in pairs.
# 
#
from trade_converter.utility import logger, get_datemode, get_record_fields, \
									get_current_path, convert_datetime_to_string, \
									is_blank_line, is_empty_cell, get_input_directory
from trade_converter.port_12307 import fix_duplicate_key_value, read_data_fields
from trade_converter.port_ftcsa import check_field_type, get_LocationAccount
from trade_converter.port_ft import convert_float_to_datetime
from xlrd import open_workbook
# from xlrd.xldate import xldate_as_datetime
from datetime import datetime
from investment_lookup.id_lookup import get_investment_Ids, \
										get_portfolio_accounting_treatment
import csv, argparse, os



class InconsistentFXTrades(Exception):
	pass



def read_transaction_file(filename):
	"""
	Note: Read the transaction file for cash transactions, a cash transaction
	includes:

	1. FXPurch, FXSale: buy one currency and sell another at the same time.
		These two transactions always occur in pairs.
	2. CashAdd: Cash deposit.
	3. CashWth: Cash withdrawal.
	4. IATCA, IATCW: cash transfers among accounts under FT control.
		These two transactions always occur in pairs.
	"""
	logger.debug('read_transaction_file(): {0}'.format(filename))

	wb = open_workbook(filename=filename)
	ws = wb.sheet_by_index(0)

	fields = read_data_fields(ws, 0)
	
	row = 1
	output = []
	transaction_type = ['FXPurch', 'FXSale', 'CashAdd', 'CashWth', 'IATCA', 'IATCW']
	while row < ws.nrows:
		if is_blank_line(ws, row):
			break

		line_info = read_line(ws, row, fields, transaction_type, validate_cash)
		if not line_info is None:
			output.append(line_info)

		row = row + 1
	# end of while loop

	return output



def read_line(ws, row, fields, transaction_type, validator):
	"""
	Read a line, create a line_info object with the information read.
	"""
	line_info = {}
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
			# cell_value = xldate_as_datetime(cell_value, get_datemode())
			cell_value = convert_float_to_datetime(cell_value)

		if fld in ['QTY', 'GROSSBAS', 'PRINB', 'RGLBVBAS', 'RGLCCYCLS', \
					'ACCRBAS', 'TRNBVBAS', 'GROSSLCL', 'FXRATE', 'TRADEPRC'] \
					and isinstance(cell_value, str) and cell_value.strip() == '':	
			cell_value = 0.0
		
		check_field_type(fld, cell_value)
		line_info[fld] = cell_value
		column = column + 1
	# end of for loop

	if transaction_type == [] or line_info['TRANTYP'] in transaction_type:
		validate_line_info(line_info)
		validator(line_info)
	else:
		line_info = None

	return line_info



def validate_cash(line_info):
	"""
	Validate a cash transaction. Actually no much to validate.
	"""
	pass




def validate_line_info(line_info):
	if line_info['STLDATE'] < line_info['TRDDATE'] \
		or line_info['ENTRDATE'] < line_info['TRDDATE']:
		logger.error('validate_line_info(): invalid dates, trade date={0}, settle day={1}, enterday={2}'.
						format(line_info['TRDDATE'], line_info['STLDATE'], line_info['ENTRDATE']))
		raise InvalidTradeInfo()

	diff = abs(line_info['GROSSBAS'] * line_info['FXRATE'] - line_info['GROSSLCL'])
	if diff > 0.01:
		logger.error('validate_line_info(): FX validation failed, diff={0}'.format(diff))
		raise InvalidTradeInfo()



def convert_to_geneva_records(output):
	records = []
	record_fields = get_record_fields()
	for trade_info in output:
		records.append(create_record(trade_info, record_fields))

	return records



def create_fx_record(trade_info, record_fields):

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



def create_fx_pairs(transaction_list):
	"""
	Since FXPurch/FXSale always occur in pairs, read the transaction_list,
	create a list of such fx buy/sell pairs.
	"""
	buy_total = 0
	sell_total = 0
	buy_list = []
	sell_list = []
	for transaction in transaction_list:
		if transaction['TRANTYP'] == 'FXPurch':
			buy_total = buy_total + transaction['GROSSBAS']
			buy_list.append(transaction)
		else if transaction['TRANTYP'] == 'FXSale':
			sell_total = sell_total - transaction['GROSSBAS']
			sell_list.append(transaction)

	if len(buy_list) != len(sell_list):
		logger.error('create_fx_pairs(): fx trades does not occur in pairs, {0} buy trades, {1} sell trades'.
						format(len(buy_list), len(sell_list)))
		raise InconsistentFXTrades()

	if abs(buy_total + sell_total) > 0.1:
		logger.error('create_fx_pairs(): fx trades does not occur in pairs, buy_total={0}, sell_total={1}'.
						format(buy_total, sell_total))
		raise InconsistentFXTrades()

	fx_pairs = []
	sell_matched_position = []
	for fx_buy in buy_list:
		pair_found = False
		position = 0
		for fx_sell in sell_list:
			if position in sell_matched_position:	# this fx sell has been matched
				position = position + 1
				continue

			if fx_buy['ACCT_ACNO'] == fx_sell['ACCT_ACNO'] \
				and fx_buy['TRDDATE'] == fx_sell['TRDDATE'] \
				and fx_buy['STLDATE'] == fx_sell['STLDATE'] \
				and abs(fx_buy['GROSSBAS'] + fx_sell['GROSSBAS']) < 0.001:
				pair_found = True
				sell_matched_position.append(position)
				fx_pairs.append((fx_buy, fx_sell))
				break

			position = position + 1
		# end of inner for loop

		if not pair_found:
			logger.error('create_fx_pairs(): no fx sell for fx buy: buy_amount={0}, currency={1}'.
						format(fx_buy['GROSSBAS'], fx_buy['LCLCCY']))
			raise InconsistentFXTrades()
	# end of outer for loop

	return fx_pairs



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
	
