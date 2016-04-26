#coding=utf-8


class JpushException(Exception):
    def __init__(self, error_msg, error_code, *args, **kwargs):
        super(JpushException, self).__init__(*args, **kwargs)
        self.error_msg = error_msg
        self.error_code = error_code

    def __str__(self):
        return "%s, error code:, %s error message: %s" % (self.__class__.__name__, str(self.error_code), str(self.error_msg))

    def __repr__(self):
        return self.__str__()