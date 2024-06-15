from .utils import get_contract_abi
class ContractWrap:
    contract_adr = None
    contract_abi = None    
    provider = None
    def __init__(self, contract_adr: str):
        self.contract_adr = contract_adr
        self.contract_details = {}
    
    @staticmethod
    async def a_init(contract_adr: str, provider: str):
        cw = ContractWrap(contract_adr)
        cw.contract_adr = contract_adr
        cw.provider = provider
        cw.contract_abi = await get_contract_abi(contract_adr, provider)
        return cw
    
    def add_abi(self, abi):
        """Adds an ABI to the contract."""
        self.contract_abi = abi
    
    def add_detail(self, key, value):
        """Adds a detail to the contract."""
        self.contract_details[key] = value

    def get_detail(self, key):
        """Retrieves a detail from the contract."""
        return self.contract_details.get(key)

    def __str__(self):
        """Returns a string representation of the contract."""
        return f"ContractWrap(adr={self.contract_adr}, details={self.contract_details})"