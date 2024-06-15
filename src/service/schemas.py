from pydantic import BaseModel, validator, Field
import re

class AnalyzeRequest(BaseModel):
    sc_address: str
    symbol: str

    @classmethod
    def is_valid_eoa_address(cls, sc_address: str):
        # Check if the address is a valid hexadecimal string
        if not re.match(r"^(0x)?[0-9a-fA-F]{40}$", sc_address):
            return False
        return True
    
    @classmethod
    def is_valid_base58_tron_address(cls, sc_address: str):
        if not re.match(r"^(T|V)[1-9A-HJ-NP-Za-km-z]{33}$", sc_address):
            return False
        return True

    @validator('sc_address')
    def validate_eoa_address(cls, address):
        if not cls.is_valid_eoa_address(address) and \
            not cls.is_valid_base58_tron_address(address):
            raise ValueError('Invalid address format')
        return address

    @validator('symbol')
    def validate_name(cls, symbol):
        if not re.match(r"^[A-Za-z0-9_-]+$", symbol.strip()):
            raise ValueError('Invalid name')
        return symbol.strip()


class PostAnalyzeRequest(AnalyzeRequest):
    provider: str
    
    @classmethod
    def is_valid_provider(cls, provider: str):
        if not provider.lower() in ['eth', 'bsc', 'trx', 'sibr']:
            return False
        return True
    
    @validator('provider')
    def validate_provider(cls, provider):
        if not cls.is_valid_provider(provider):
            raise ValueError('Invalid provider')
        return provider.lower()


class QueryParams(BaseModel):
    param1: str = Field(..., min_length=3, max_length=50)  # required parameter with length constraints
    param2: int = Field(ge=0, le=100)  # optional integer parameter with range 0-100
