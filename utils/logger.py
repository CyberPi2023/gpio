#-*- coding=utf-8 -*-

import logging


class Formatter(logging.Formatter):

    def format(self, record):

        result = logging.Formatter.format(self, record)

        # Replace the original format with one customized by logging level
        if record.levelno == logging.DEBUG:
            pass

        elif record.levelno == logging.INFO:
            pass

        elif record.levelno == logging.ERROR:
            result = '❌  ' + str(result)

        elif record.levelno == logging.WARNING:
            result = '⚠️  ' + str(result)

        return result


class Logger(logging.getLoggerClass()):
    '''
      自定义 Log，自带颜色
    '''

    def __init__(self, name):
        logging.getLoggerClass().__init__(self, name, logging.DEBUG)

        handler = logging.StreamHandler()
        handler.setLevel(logging.DEBUG)
        handler.setFormatter(Formatter("[%(levelname)s][%(name)s:%(lineno)d] %(message)s"))

        self.addHandler(handler)
