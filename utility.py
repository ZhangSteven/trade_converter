# coding=utf-8
# 
# from config_logging package, provides a config object (from config file)
# and a logger object (logging to a file).
# 
import logging
import configparser
import os



def get_current_path():
	"""
	Get the absolute path to the directory where this module is in.

	This piece of code comes from:

	http://stackoverflow.com/questions/3430372/how-to-get-full-path-of-current-files-directory-in-python
	"""
	return os.path.dirname(os.path.abspath(__file__))



def _load_config(filename='tc.config'):
	"""
	Read the config file, convert it to a config object. The config file is 
	supposed to be located in the same directory as the py files, and the
	default name is "config".

	Caution: uncaught exceptions will happen if the config files are missing
	or named incorrectly.
	"""
	path = get_current_path()
	config_file = path + '\\' + filename
	# print(config_file)
	cfg = configparser.ConfigParser()
	cfg.read(config_file)
	return cfg



# initialized only once when this module is first imported by others
if not 'config' in globals():
	config = _load_config()



def convert_log_level(log_level):
	"""
	Convert the log level specified in the config file to the numerical
	values required by the logging module.
	"""
	if log_level == 'debug':
		return logging.DEBUG
	elif log_level == 'info':
		return logging.INFO
	elif log_level == 'warning':
		return logging.WARNING
	elif log_level == 'error':
		return logging.ERROR
	elif log_level == 'critical':
		return logging.CRITICAL
	else:
		return logging.DEBUG



def _setup_logging():
    """ 
    Setup logging parameters, supposed to be called only once.

    Original code from:
    https://gimmebar-assets.s3.amazonaws.com/4fe38b76be0a5.html
    """

    # use the config object
    global config

    fn = config['logging']['log_file']
    fn = get_current_path() + '\\' + fn
    # print(fn)
    fmt='%(asctime)s - %(module)s - %(levelname)s: %(message)s'
    log_level = config['logging']['log_level']
    log_level = convert_log_level(log_level)

    logging.basicConfig(level=log_level, filename=fn, format=fmt)
    return logging.getLogger('root')



# initialized only once when this module is first imported by others
if not 'logger' in globals():
	logger = _setup_logging()



def get_datemode():
	"""
	Read datemode from the config object and return it (in integer)
	"""
	global config
	d = config['excel']['datemode']
	try:
		datemode = int(d)
	except:
		logger.error('get_datemode(): invalid datemode value: {0}'.format(d))
		raise

	return datemode
