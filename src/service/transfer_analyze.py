import logging
import re
from browniecheck.dorealcheck import append_main_function, generate_brownie_config, get_brownie_ouput
from contractdata.utils import get_sibr_token_holders
from seleniumwrap.bscscan_by_address import scrap_holders_of_bsc_token
from seleniumwrap.etherscan_by_address import scrap_holders_of_eth_token
from web3wrap.utils import a_get_pool_liqudity_for_contrtact

async def sc_transfer_analyze(sc_address: str, provider: str, session):
    try:
        #holders information
        if provider == 'eth':
            holders = scrap_holders_of_eth_token(sc_address)
        elif provider == 'bsc':
            holders = scrap_holders_of_bsc_token(sc_address)
        elif provider == 'sibr':
            holders = await get_sibr_token_holders(sc_address)
        if holders and len(holders) > 0:
            holders_check_num : int = 6
            if provider == 'sibr':
                holders_check_num : int = 2
                brownie_config = {"networks" : 
                        {"default": "sibrnet",
                          "sibrnet":{
                                    # "fork": "https://rpc.test.siberium.net",
                                    "cmd_settings": 
                                    {"unlock": [holders[sc_address][holders_check_num].get("address","0x0000000000000000000000000000000000000000")],}
                                }
                        },
                    }
            elif provider == 'eth':
                brownie_config = {"networks" : 
                        {"default": "mainnet-fork",
                          "mainnet-fork":{
                                    # "fork": "http://eth-node-dev.kyt:8545",
                                    "fork": "https://mainnet.infura.io/v3/b673126bbeee4604ba4421c92ccbf219",
                                    "cmd_settings": 
                                    {"unlock": [holders[sc_address][holders_check_num].get("address","0x0000000000000000000000000000000000000000")],}
                                }
                        },
                        "dotenv": ".env"
                    }
            elif provider == 'bsc':
                brownie_config = {"networks" : 
                        {"default": "bsc-main-fork",
                          "bsc-main-fork": 
                                {"cmd_settings": 
                                    {"unlock": [holders[sc_address][holders_check_num].get("address","0x0000000000000000000000000000000000000000")],}
                                }
                        }
                    }
            print(brownie_config)
            generate_brownie_config(brownie_config)
            append_main_function(sc_address, 
                                 holders[sc_address][holders_check_num].get("address","0x0000000000000000000000000000000000000000"), 
                                 provider)
        
        brownie_result = await get_brownie_ouput("check_transfer")
        result_match = re.search(r'result: (.+)', brownie_result['output'])
        transfer_result = result_match.group(1) if result_match else None
        print(transfer_result)
        
        if transfer_result is not None:
            transfer_delivered = float(transfer_result.split('@')[0].strip())
            transfer_percent = float(transfer_result.split('@')[1].strip())
    
            result = {
                'transfer_info': {
                    'transfer_percent': {
                        'value': transfer_percent,
                        'status': (lambda transfer_percent: 1 if transfer_percent == 0 else (3 if transfer_percent > 5 else 2))(transfer_percent)
                    },
                    'transfer_delivered': {
                        'value': transfer_delivered,
                        'status': (lambda transfer_delivered: 1 if transfer_delivered > 98 else (3 if transfer_delivered >= 95 else 2))(transfer_delivered)
                    },
                }
            }
        
        return result
        
    except RuntimeError as runtime_error:
        # await operation_aireq_dao.stmt_delete_ai_request_by_adr(sc_address)
        raise runtime_error
    except Exception as e:
        logging.error(F"Error! API  response error: {e}")
        raise RuntimeError(F"Error! API base_analyze_sc response error: {e}")