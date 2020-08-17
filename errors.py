class ResponseError(Exception):
    def __init__(self, code):
        self.code = code
        self.message = "Error, server returned code"
        super().__init__(self.message)
    def __str__(self):
        return f"{self.message}: {self.code}"
class ArrayLengthError(Exception):
    def __init__(self, length):
        self.message = "Internal error"
        self.length = length
        super().__init__(self.message)
    def __str__(self):
        return f"{self.message}: data loader has failed, expected array length: 1, got {self.length}"
class LoginError(Exception):
    def __init__(self):
        self.message = "Error"
        super().__init__(self.message)
    def __str__(self):
        return f"{self.message}: Login has failed"
class UnimplementedError(Exception):
    def __init__(self):
        self.message = "Error"
        super().__init__(self.message)
    def __str__(self):
        return f"{self.message}: Feature not yet implemented due to the current lack of data"