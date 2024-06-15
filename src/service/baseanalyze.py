import logging

from sympy import N, re
#from coingeko.coingeko_api import download_token_common_info, get_token_id
from contractdata.utils import contract_creator_adr, contract_proxy_status, get_contract_name, get_contract_source_code
from exceptions import NoContractError
#from google.search import search_for_links
from seleniumwrap.bscscan_by_address import scrap_holders_of_bsc_token
from seleniumwrap.etherscan_by_address import scrap_holders_of_eth_token
from web3wrap.utils import adr_balance_in_contract_tokens, contract_owner_balance_rate, is_adr_dead_or_null_or_unreal, a_get_pool_liqudity_for_contrtact, mint_burn_destruct_func_detect
from contractdata.contractwrap import ContractWrap

async def sc_base_analyze(sc_address: str, provided_symbol:str, provider: str, session):
    # operation_aireq_dao = AIReqDAO(session)    
    # if await operation_aireq_dao.stmt_exist_ai_request(sc_address):
    #     airequest: AIRequest = await operation_aireq_dao.get_ai_request(sc_address)
    #     if not bool(airequest.handled):
    #         raise ProcessingError(f"Token with address {sc_address} is already in progress")
    #     elif ready_answer := await operation_aireq_dao.exists_token_report(sc_address):
    #         return ready_answer
    _token_symbol = provided_symbol
    try:
        cw = await ContractWrap.a_init(sc_address, provider)
        if cw.contract_abi is None:
            raise NoContractError(f"Abi or source code for contract {sc_address} not found")
        contract_main_analytic: dict = {'creator': {'adr': None, 'balance': None, 'rate': None},
                                        'creator_balance_rate': {'value': None, 'status': 0},
                                        'owner': {'adr': None, 'balance': None, 'rate': None},
                                        'owner_balance_rate': {'value': None, 'status': 0},
                                        'is_renounced': {'value': None, 'status': 0},
                                        'is_mintable': {'value': None, 'status': 0},
                                        'is_burnable': {'value': None, 'status': 0},
                                        'is_proxy': {'value': None, 'status': 0},
                                        'is_self_destructable': {'value': None, 'status': 0},
                                        'has_source_code': False,
                                        'is_token_transferable': {'value': None, 'status': 0},
                                        'transer_tax': {'value': None, 'status': 0},
                                        'transfer_from_tax': {'value': None, 'status': 0},
                                        }         
        #owner statstics
        if provider in ["eth", "bsc"]:
            owner_result = await contract_owner_balance_rate(sc_address, provider, cw.contract_abi)
            if owner_result:
                contract_main_analytic['owner']['adr'], \
                contract_main_analytic['owner']['balance'], \
                contract_main_analytic['owner']['rate'] = owner_result
                
                owner_balance_rate = contract_main_analytic['owner']['rate']
                if owner_balance_rate is not None:
                    contract_main_analytic['owner_balance_rate']['value'] = owner_balance_rate
                    if owner_balance_rate > 10:
                        contract_main_analytic['owner_balance_rate']['status'] = 2
                    else:
                        contract_main_analytic['owner_balance_rate']['status'] = 1
        
        owner_address = contract_main_analytic['owner']['adr']
        #creator statistics
        creator_adr = await contract_creator_adr(sc_address, provider)
        if creator_adr == owner_address:
            contract_main_analytic['creator'] = contract_main_analytic['owner']
            contract_main_analytic['creator_balance_rate'] = contract_main_analytic['owner_balance_rate']
        else:
            contract_main_analytic['creator']['adr'] = creator_adr
            creator_result = await adr_balance_in_contract_tokens(creator_adr, sc_address, provider, cw.contract_abi)
            if creator_result:
                _, \
                contract_main_analytic['creator']['balance'], \
                contract_main_analytic['creator']['rate'] = creator_result
            
            creator_balance_rate = contract_main_analytic['creator']['rate']
            if creator_balance_rate is not None:
                contract_main_analytic['creator_balance_rate']['value'] = creator_balance_rate
                if creator_balance_rate > 10:
                    contract_main_analytic['creator_balance_rate']['status'] = 2
                else:
                    contract_main_analytic['creator_balance_rate']['status'] = 1
                
        #renounce_check
        if owner_address is not None:
            _res = await is_adr_dead_or_null_or_unreal(owner_address)
            contract_main_analytic['is_renounced']['value'] = _res
            if _res is not None:
                if _res is False:
                    contract_main_analytic['is_renounced']['status'] = 2
                else:
                    contract_main_analytic['is_renounced']['status'] = 1
        
        _res_m_b_d_dict = await mint_burn_destruct_func_detect(sc_address, provider, cw.contract_abi)
        if _res_m_b_d_dict is not None:
            if contract_main_analytic['is_renounced']['value']:
                contract_main_analytic['is_mintable']['value'] = False
                contract_main_analytic['is_mintable']['status'] = 1
                contract_main_analytic['is_burnable']['value'] = False
                contract_main_analytic['is_burnable']['status'] = 1
            else:
                contract_main_analytic['is_mintable']['value']  = _res_m_b_d_dict['can_mint']
                if _res_m_b_d_dict['can_mint']:
                    contract_main_analytic['is_mintable']['status'] = 2
                else:
                    contract_main_analytic['is_mintable']['status'] = 1
            
                contract_main_analytic['is_burnable']['value'] = _res_m_b_d_dict['can_burn']
                if contract_main_analytic['is_burnable']['value']:
                    contract_main_analytic['is_burnable']['status'] = 2
                else:
                    contract_main_analytic['is_burnable']['status'] = 1
            
            contract_main_analytic['is_self_destructable']['value'] = _res_m_b_d_dict['can_self_destruct']
            if contract_main_analytic['is_self_destructable']['value']:
                contract_main_analytic['is_self_destructable']['status'] = 2
            else:
                contract_main_analytic['is_self_destructable']['status'] = 1
        
        # get proxy status
        _res = await contract_proxy_status(sc_address, provider)
        contract_main_analytic['is_proxy']['value'] = _res
        if _res is not None:
            if _res is True:
                contract_main_analytic['is_proxy']['status'] = 2
            else:
                contract_main_analytic['is_proxy']['status'] = 1
        
        contract_code = await get_contract_source_code(sc_address, provider)
        if (contract_code is not None) and ('SourceCode' in contract_code):
            contract_main_analytic['has_source_code'] = True
            
            sc_token_symbol = contract_code.get("ContractName", "")
            if len(sc_token_symbol) > 0:
                contract_main_analytic['token_symbol'] = sc_token_symbol
            
            # probable_token_id = await search_for_links(sc_address, siteSearch="coingecko.com") 
            # if probable_token_id is None:
            #     probable_token_id = await get_token_id(sc_token_symbol.lower().replace("token", ""))
            
            # if probable_token_id is not None:
            #     contract_main_analytic['token_id'] = probable_token_id
            #     contract_main_analytic = {**contract_main_analytic, **(await download_token_common_info(probable_token_id))}
        
        #liquidty statistics
        # if provider in ["eth", "bsc"]:
        #     liqudity_pool_info :dict = await a_get_pool_liqudity_for_contrtact(sc_address, provider)
        return contract_main_analytic
        
    except RuntimeError as runtime_error:
        # await operation_aireq_dao.stmt_delete_ai_request_by_adr(sc_address)
        raise runtime_error
    except NoContractError as no_contract_error:
        logging.error(F"Error! API  response error: {no_contract_error}")
        raise no_contract_error
    except Exception as e:
        logging.error(F"Error! API  response error: {e}")
        raise RuntimeError(F"Error! API base_analyze_sc response error: {e}")
