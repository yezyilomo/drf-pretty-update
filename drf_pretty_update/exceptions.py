
class DRFPrettyUpdateException(Exception):
    """Base class for exceptions in this module."""


class InvalidOperation(DRFPrettyUpdateException):
    """Invalid Operation."""