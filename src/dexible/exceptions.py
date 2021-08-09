class DexibleException(Exception):
    pass


class DexibleOrderException(DexibleException):
    pass


class InvalidOrderException(DexibleOrderException):
    pass


class OrderIncompleteException(DexibleOrderException):
    pass


class QuoteMissingException(DexibleOrderException):
    pass


class DexibleAlgoException(DexibleException):
    pass
