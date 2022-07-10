import logging
import inspect


class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class Logger(metaclass=Singleton):

    def __init__(self, name='logger', level=logging.DEBUG):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)

        fh = logging.FileHandler('%s.log' % name, 'w')
        self.logger.addHandler(fh)

        sh = logging.StreamHandler()
        self.logger.addHandler(sh)

    @staticmethod
    def __get_call_info():
        stack = inspect.stack()

        fn = stack[2][1]
        ln = stack[2][2]
        func = stack[2][3]

        return fn, func, ln

    def debug(self, msg):
        message = "[DEBUG {} - {} at line {}]: {}".format(*self.__get_call_info(), msg)
        self.logger.debug(message)

    def info(self, msg):
        message = "[INFO {} - {} at line {}]: {}".format(*self.__get_call_info(), msg)
        self.logger.info(message)

    def warning(self, msg):
        message = "[WARNING {} - {} at line {}]: {}".format(*self.__get_call_info(), msg)
        self.logger.warning(message)

    def error(self, msg):
        message = "[ERROR {} - {} at line {}]: {}".format(*self.__get_call_info(), msg)
        self.logger.error(message)
