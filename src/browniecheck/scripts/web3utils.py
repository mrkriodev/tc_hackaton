#from .config import BSCSCAN_API_KEY, ETHERSCAN_API_KEY
import requests
import json
BSCSCAN_API_KEY = "CH6W15GK3EDH3W13IJFAHNZY37GMYZ8NM7"
ETHERSCAN_API_KEY = "DUQ3IPIYBDIDQCW6XTIF5HZ6HGF4III6CV"


def get_contract_abi(contract_address, provider: str):
    api_key = ETHERSCAN_API_KEY
    service_url = f"https://api.etherscan.io/api?module=contract&action=getabi&address={contract_address}&apikey={api_key}"
    if provider.lower() == "bsc":
        api_key = BSCSCAN_API_KEY
        service_url = f"https://api.bscscan.com/api?module=contract&action=getabi&address={contract_address}&apikey={api_key}"

    response = requests.get(service_url)
    data = response.json()
    if data['status'] == '1' and data['message'] == 'OK':
        return json.loads(data['result'])
    else:
        raise Exception("Failed to get ABI for contract")
