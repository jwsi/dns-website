class ControlledException(Exception):
    """
    Controlled exception class.
    """
    def __init__(self, status):
        """
        Constructor for the controlled exception class.
        """
        self.status = status