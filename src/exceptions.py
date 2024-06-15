import logging

class ProcessingError(Exception):
    def __init__(self, message):
        logging.error(F"Processing error | {message}")
        self.message = message
        super().__init__(self.message)
        
class NoContractError(Exception):
    def __init__(self, message):
        logging.error(F"No contract error | {message}")
        self.message = message
        super().__init__(self.message)