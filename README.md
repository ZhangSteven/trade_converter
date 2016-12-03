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

1. Consider separate logging and config function into two modules, each project can have its own config module, while all projects can share the same logging module? -- test: get two test modules running at the same time, but
log to different files.

2. Put a "directory" into config file, as the directory for input trade files or folder. -- we don't want the input/output to pollute the project directory.

1. Add error testing code, make sure the errors are generated as expected.



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