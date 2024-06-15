import aiohttp
import json
from src.config import ETHERSCAN_API_KEY, BSCSCAN_API_KEY, TRONSCAN_API_KEY
from src.gpt.utils import base64tostr
from typing import Optional

# def get_contract_source_code(api_key, address)->dict:
#     # create an empty list to hold the source code for each contract
#     # source_codes = []

#     base_url = "https://api.etherscan.io/api?module=contract&action=getsourcecode"

#     full_url = f"{base_url}&address={address}&apikey={api_key}"
#     response = requests.get(full_url)
#     data = response.json()
#     source_code = data["result"][0]    
#     return source_code    

async def get_contract_abi(contract_address, provider: str):
    api_key = ETHERSCAN_API_KEY
    service_url = f"https://api.etherscan.io/api?module=contract&action=getabi&address={contract_address}&apikey={api_key}"
    if provider.lower() == "bsc":
        api_key = BSCSCAN_API_KEY
        service_url = f"https://api.bscscan.com/api?module=contract&action=getabi&address={contract_address}&apikey={api_key}"
    if provider.lower() == "sibr":
        service_url = f"https://explorer.test.siberium.net/api?module=contract&action=getabi&address={contract_address}"
    
    async with aiohttp.ClientSession() as session:
        async with session.get(service_url) as response:
            data = await response.json()
            if data['status'] == '1' and data['message'] == 'OK':
                return json.loads(data['result'])
            else:
                # raise Exception("Failed to get ABI for contract")
                return None

async def get_contract_source_code(address, provider) -> dict:
    # create an empty list to hold the source code for each contract
    # source_codes = []
    source_code: dict = {}
    if provider == "trx":
        # api_key = TRONSCAN_API_KEY
        base_url = "https://apilist.tronscanapi.com/api/solidity/contract/info"
        async with aiohttp.ClientSession() as session:
            async with session.post(base_url, json={"contractAddress": address}) as response:
                data = await response.json()
        
        internal_data = data["data"]
        contract_code: list = internal_data.get("contract_code", [])
        if len(contract_code):
            contract_code_items: dict = contract_code[0]
            base64_contract_code = contract_code_items.get("code","")
            if len(base64_contract_code):
                source_code['SourceCode'] = base64tostr(base64_contract_code)
        source_code['ContractName'] = internal_data.get("contract_name")
        
    else:
        _headers = {
            "Connection": "keep-alive",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept": "*/*",
            "User-Agent": "PostmanRuntime/7.34.0"
        }
        api_key = ETHERSCAN_API_KEY
        base_url = "https://api.etherscan.io/api?module=contract&action=getsourcecode"
        
        if provider == "bsc":
            _headers = {
                "Connection": "keep-alive",
                "Accept-Encoding": "gzip, deflate, br",
                "Accept": "*/*",
            }
            api_key = BSCSCAN_API_KEY
            base_url = "https://api.bscscan.com/api?module=contract&action=getsourcecode"
        
        if provider == "sibr":
            base_url = "https://explorer.test.siberium.net/api?module=contract&action=getsourcecode"
        
        full_url = f"{base_url}&address={address}&apikey={api_key}"

        async with aiohttp.ClientSession() as session:
            async with session.get(full_url, headers=_headers) as response:
                data = await response.json()

        source_code = data["result"][0]
    
    return source_code


async def get_contract_name(address, provider, ) -> str:
    source_code = await get_contract_source_code(address, provider)
    return source_code.get("ContractName", "")


async def contract_creator_adr(contract_address, provider) -> Optional[str]:
    creator_adr = None
    try:
        if provider == "trx" or provider == "sibr":
            pass
        else:
            _headers = {
                    "Connection": "keep-alive",
                    "Accept-Encoding": "gzip, deflate, br",
                    "Accept": "*/*",
                }

            api_key = ETHERSCAN_API_KEY
            base_url = "https://api.etherscan.io/api?module=contract&action=getcontractcreation"
            if provider == "bsc":
                api_key = BSCSCAN_API_KEY
                base_url = "https://api.bscscan.com/api?module=contract&action=getcontractcreation"
            full_url = f"{base_url}&contractaddresses={contract_address}&apikey={api_key}"

            async with aiohttp.ClientSession() as session:
                async with session.get(full_url, headers=_headers) as response:
                    data_result = await response.json()
            if data_result.get("message") == "OK":
                creator_adr = data_result["result"][0]["contractCreator"]
    except Exception as e:
        print(f"{__file__}: {str(e)}")
    finally:
        return creator_adr
    

async def contract_proxy_status(contract_address, provider) -> Optional[bool]:
    status = None
    try:
        if provider == "trx" or provider == "sibr":
            pass
        else:
            _headers = {
                    "Connection": "keep-alive",
                    "Accept-Encoding": "gzip, deflate, br",
                    "Accept": "*/*",}
            api_key = ETHERSCAN_API_KEY
            base_url = "https://api.etherscan.io/api?module=contract&action=verifyproxycontract"
            if provider == "bsc":
                api_key = BSCSCAN_API_KEY
                base_url = "https://api.bscscan.com/api?module=contract&action=verifyproxycontract"
                
            full_url = f"{base_url}&apikey={api_key}"
            
            async with aiohttp.ClientSession() as session:
                async with session.post(full_url, data={'address': contract_address}) as response:
                    data_result = await response.json()
            if int(data_result.get("status", "0")) == 1 and data_result.get("message") == "OK":
                check_guid = data_result["result"]
                
                api_key = ETHERSCAN_API_KEY
                base_url = "https://api.etherscan.io/api?module=contract&action=checkproxyverification"
                if provider == "bsc":
                    api_key = BSCSCAN_API_KEY
                    base_url = "https://api.bscscan.com/api?module=contract&action=checkproxyverification"
                
                full_url = f"{base_url}&guid={check_guid}&apikey={api_key}"
                
                data_result={}
                async with aiohttp.ClientSession() as session:
                    async with session.get(full_url, headers=_headers) as response:
                        data_result = await response.json()
                if data_result.get("message","") == "OK":
                    status = True
                elif data_result.get("message","") == "NOTOK" and \
                    int(data_result.get("status", -1)) == 0:
                        status = True
                else:
                    status = False

    except Exception as e:
        print(f"{__file__}: {str(e)}")
    finally:
        return status
    
    
async def get_sibr_token_holders(sc_address) -> dict:
    
    base_url = "https://explorer.test.siberium.net/api?module=token&action=getTokenHolders"
        
    full_url = f"{base_url}&contractaddress={sc_address}"

    async with aiohttp.ClientSession() as session:
        async with session.get(full_url) as response:
            data = await response.json()

    holders = data["result"]
    
    return {sc_address: holders}