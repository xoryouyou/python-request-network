class InvalidRequestParameters(Exception):
    pass


class TokenNotSupported(Exception):
    pass


class UnsupportedCurrency(BaseException):
    pass


class RequestNotFound(BaseException):
    pass


class TransactionNotFound(BaseException):
    pass


class IPFSConnectionFailed(BaseException):
    pass


class RoleNotSupported(BaseException):
    pass


class ArtifactNotFound(BaseException):
    pass
