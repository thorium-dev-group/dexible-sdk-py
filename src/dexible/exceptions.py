class DexibleException(Exception):
    def __init__(self, message="", request_id=None, json_response=None, *args, **kwargs):
        self.message = message
        self.request_id = request_id
        self.json_response = json_response

        if request_id is None and \
                type(json_response) == dict and \
                'requestId' in json_response:
            self.request_id = json_response['requestId']
        super(DexibleException, self).__init__(*args, **kwargs)


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
