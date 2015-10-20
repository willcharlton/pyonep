""" 
    Defines some constants, such as logging formatter, for use across all modules.
"""

from logging import Formatter
form = '%(asctime)s-%(levelname)s-%(name)s:%(funcName)s:%(lineno)d ::> %(message)s'
formatter = Formatter(form)
