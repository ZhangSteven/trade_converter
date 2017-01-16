# trade_converter

Convert the 12307 portfolio's trade file format to Advent Geneva system's trade quick import format.

+++++++++++
How to use
+++++++++++

To convert a single trade file to upload format, use

	python tc.py <portfolio_code> --file <trade_file>

To convert multiple trade files under a directory, use

	python tc.py <portfolio_code> --folder <folder_name>

To run unit test, use

	nose2


+++++++++++
Todo
+++++++++++
1. Add error testing code, make sure the errors are generated as expected.

2. Consider move the isin code to ticker lookup to investment_lookup project.

3. Find out why US treasury bond/note trade has inconsistency, only in 12528 portfolio.




+++++++++++
ver 0.13
+++++++++++
1. Add module port_ft.py for FT historical trades, works for all purchase/sale trades except a few US treasury bond/note trades in 12528 portfolio.



+++++++++++
ver 0.12
+++++++++++
1. Add a broker mapping function to map the old broker code to the new ones, so that since 2016-12-13, trades are loaded into Geneva with the new broker code.

2. Some development code for port_overseas_bond.py.



+++++++++++
ver 0.1101
+++++++++++
1. No change in program code, just add one more entry "762 HK" to investment lookup file.



+++++++++++
ver 0.11
+++++++++++

1. Add two entries in the config file:

	> base directory for input trade files or folder. So those trade files can be in a different directory.

	> base directory for the log file. So during production deployment, the log file can be put in a different directory for easy checking.

2. logging function is handled by another package config_logging.



+++++++++++
ver 0.1
+++++++++++

1. Either the single trade file or folder must be under the same directory where tc.py resides.

2. Only trade file format for portfolio 12307 is supported at the moment. If more portfolios are needed, implement another module like port_12307.py.