import logging

LOG_FILE = "../logs/pythia.log"
LOG_LEVEL = logging.DEBUG

##########################################################################
#  define a python logger to be used in the app                          #
##########################################################################
logger = logging.getLogger('delphi')
logger.setLevel(LOG_LEVEL)
# define handlers to write messages to the log file and the console
file_handler = logging.FileHandler(LOG_FILE) # type: ignore
console_handler = logging.StreamHandler()
# define and set the format for the log messages
formatter = logging.Formatter('%(asctime)s - %(filename)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

# add the defined handlers to the logger
logger.addHandler(file_handler)
logger.addHandler(console_handler)