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
ver 0.1
+++++++++++

1. Either the single trade file or folder must be under the same directory where tc.py resides.

2. Only trade file format for portfolio 12307 is supported at the moment. If more portfolios are needed, implement another module like port_12307.py.