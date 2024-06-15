import json
import numpy as np
from web3 import Web3
#from web3 import AsyncWeb3
#from web3.providers.async_rpc import AsyncHTTPProvider
#from web3.middleware.geth_poa import async_geth_poa_middleware
import asyncio
import logging
from contractdata.utils import get_contract_abi
from src.config import INFURA_API_KEY
from .math_utils import get_token_amounts, nearest_numbers_divisible_by_figure, get_price_from_sqrt_price, uniswap_v3_tick_to_price
from typing import Optional, Tuple

logging.basicConfig(level=logging.INFO)
requests_log = logging.getLogger("requests.packages.urllib3")
requests_log.setLevel(logging.INFO)
requests_log.propagate = True

null_adr = "0x0000000000000000000000000000000000000000"
dead_adr = "0x000000000000000000000000000000000000dead"

# async def a_contract_owner_balance(contract_address, provider):
#     infura_url = f"https://mainnet.infura.io/v3/{INFURA_API_KEY}"
#     # Using AsyncHTTPProvider for asynchronous web3 calls
#     web3 = AsyncWeb3(AsyncHTTPProvider(endpoint_uri=infura_url))
#     web3.middleware_onion.inject(async_geth_poa_middleware, layer=0)
#     try:
#         if not web3.is_connected():
#             raise Exception("Failed to connect to Ethereum network")
#         abi = await get_contract_abi(contract_address, provider)        
#         contract = web3.eth.contract(address=contract_address, abi=abi)
#         owner_address = await contract.functions.owner().call()
#         balance = float(await contract.functions.balanceOf(owner_address).call())
#         decimals = await contract.functions.decimals().call()
#         owner_balance = balance / (10 ** decimals)
#         print(f"Balance: {owner_balance} tokens")
#         return owner_balance
#     except Exception as e:
#         print(f"Error: {e}")
#         return None

async def get_contract_code(contract_address, provider: str):
    provider_url = f"https://mainnet.infura.io/v3/{INFURA_API_KEY}"
    
    if provider == "bsc":
        provider_url = "https://bsc-dataseed.binance.org"
        #provider_url = "http://10.32.20.24:8545"
    web3 = Web3(Web3.HTTPProvider(provider_url))

    fixed_contract_address = web3.to_checksum_address(contract_address)
    try:
        if not web3.is_connected():
            raise Exception("Failed to connect to Ethereum network")
        
        #cntr_abi = await get_contract_abi(fixed_contract_address, provider)
        
        #contract = web3.eth.contract(address=fixed_contract_address, abi=cntr_abi)
        bytecode = web3.eth.get_storage_at(fixed_contract_address, 0)
        print(f"storage at 0: {bytecode.hex()}")
         
    except Exception as e:
        print(f"Error: {e}")
        return None

async def adr_balance_in_contract_tokens(check_adr, contract_address, provider, cntr_abi_in=None) -> Optional[Tuple[str, int, float]]:
    provider_url = f"https://mainnet.infura.io/v3/{INFURA_API_KEY}"
    
    if provider == "bsc":
        provider_url = "https://bsc-dataseed.binance.org"
        #provider_url = "http://10.32.20.24:8545"
    web3 = Web3(Web3.HTTPProvider(provider_url))

    fixed_contract_address = web3.to_checksum_address(contract_address)
    fixed_check_adr = web3.to_checksum_address(check_adr)
    try:
        if not web3.is_connected():
            raise Exception("Failed to connect to blockchain network")
        
        # # min_owner_abi = '[{"inputs":[],"outputs":[{"internalType":"uint8","name":"","type":"uint8"}],"name":"decimals"}, {"inputs":[],"name":"owner","outputs":[{"internalType":"address","name":"","type":"address"}],"payable":false,"stateMutability":"view","type":"function"}, {"inputs":[{"internalType":"address","name":"account","type":"address"}],"name":"balanceOf","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"totalSupply","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"}]'
        # min_balance_abi = '[{"inputs":[],"name":"decimals","outputs":[{"internalType":"uint8","name":"","type":"uint8"}],"stateMutability":"view","type":"function"}, {"inputs":[{"internalType":"address","name":"account","type":"address"}],"name":"balanceOf","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"totalSupply","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"}]'
        if cntr_abi_in != None:
            cntr_abi = cntr_abi_in
        else:
            cntr_abi = await get_contract_abi(fixed_contract_address, provider)
            # cntr_abi = min_balance_abi
        
        contract = web3.eth.contract(address=fixed_contract_address, abi=cntr_abi)
        decimals = contract.functions.decimals().call()
        
        adr_balance = float(contract.functions.balanceOf(fixed_check_adr).call())
        total = float(contract.functions.totalSupply().call())
        adr_rate = round((adr_balance / total)*100, 2)
        
        return (fixed_check_adr, adr_balance/(10**decimals), adr_rate)
    except Exception as e:
        print(f"Error: {e}")
        return None

async def contract_owner_balance_rate(contract_address, provider, cntr_abi_in=None) -> Optional[Tuple[str, int, float]]:
    provider_url = f"https://mainnet.infura.io/v3/{INFURA_API_KEY}"
    
    if provider == "bsc":
        provider_url = "https://bsc-dataseed.binance.org"
        #provider_url = "http://10.32.20.24:8545"
    web3 = Web3(Web3.HTTPProvider(provider_url))

    fixed_contract_address = web3.to_checksum_address(contract_address)
    try:
        if not web3.is_connected():
            raise Exception("Failed to connect to blockhain network")
        
        # min_owner_abi = '[{"inputs":[],"name":"decimals","outputs":[{"internalType":"uint8","name":"","type":"uint8"}],"stateMutability":"view","type":"function"}, {"inputs":[],"name":"owner","outputs":[{"internalType":"address","name":"","type":"address"}],"payable":false,"stateMutability":"view","type":"function"}, {"inputs":[{"internalType":"address","name":"account","type":"address"}],"name":"balanceOf","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"totalSupply","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"}]'
        # #min_owner_abi = '[{"inputs":[],"name":"decimals","outputs":[{"internalType":"uint8","name":"","type":"uint8"}],"stateMutability":"view","type":"function"}, {"inputs":[],"name":"owner","outputs":[{"internalType":"address","name":"","type":"address"}],"payable":false,"stateMutability":"view","type":"function"}, {"inputs":[{"internalType":"address","name":"account","type":"address"}],"name":"balanceOf","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"totalSupply","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"}]'
        if cntr_abi_in != None:
            cntr_abi = cntr_abi_in
        else:
            cntr_abi = await get_contract_abi(fixed_contract_address, provider)
            # cntr_abi = min_owner_abi
        
        contract = web3.eth.contract(address=fixed_contract_address, abi=cntr_abi)

        owner_address = contract.functions.owner().call()
        owner_balance = float(contract.functions.balanceOf(owner_address).call())
        
        decimals = contract.functions.decimals().call()
        total = float(contract.functions.totalSupply().call())
        owner_rate = round((owner_balance / total)*100, 2)
        
        return (owner_address.lower(), owner_balance/(10**decimals), owner_rate)
    except Exception as e:
        print(f"Error: {e}")
        return None

async def mint_burn_destruct_func_detect(contract_address, provider, cntr_abi_in = None):
    provider_url = f"https://mainnet.infura.io/v3/{INFURA_API_KEY}"
    if provider == "bsc":
        provider_url = "https://bsc-dataseed.binance.org"
    web3 = Web3(Web3.HTTPProvider(provider_url))
    fixed_contract_address = web3.to_checksum_address(contract_address)
    try:
        if not web3.is_connected():
            raise Exception("Failed to connect to blockhain network")
        if cntr_abi_in != None:
            cntr_abi = cntr_abi_in
        else:
            cntr_abi = await get_contract_abi(fixed_contract_address, provider)
        
        if cntr_abi is None:
            return None
        
        result_dict = {'can_mint': False, 'can_burn': False, 'can_self_destruct': False}
        for item in cntr_abi:
            if item.get('type') != 'function':
                continue
            if 'mint' in item.get('name', "").lower():
                result_dict['can_mint'] = True
            elif 'burn' in item.get('name', "").lower():
                result_dict['can_burn'] = True
            elif 'destruct' in item.get('name', "").lower():
                result_dict['can_self_destruct'] = True
        
        return result_dict
    except Exception as e:
        print(f"Error: {e}")
        return None

# async def test_transfer_now(contract_address, provider):
#     provider_url = f"https://mainnet.infura.io/v3/{INFURA_API_KEY}"
    
#     if provider == "bsc":
#         provider_url = "https://bsc-dataseed.binance.org"
#         #provider_url = "http://10.32.20.24:8545"
#     web3 = Web3(Web3.HTTPProvider(provider_url))

#     fixed_contract_address = web3.to_checksum_address(contract_address)
#     try:
#         if not web3.is_connected():
#             raise Exception("Failed to connect to Ethereum network")
        
#         min_transfer_abi = '[{"constant":false,"inputs":[{"name":"_to","type":"address"},{"name":"_value","type":"uint256"}],"name":"transfer","outputs":[],"payable":false,"stateMutability":"nonpayable","type":"function"}, {"inputs":[{"internalType":"address","name":"account","type":"address"}],"name":"balanceOf","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"}]'
#         cntr_abi = min_transfer_abi
#         contract = web3.eth.contract(address=fixed_contract_address, abi=cntr_abi)
        
#         contract.functions.transfer().call()
        
#     except Exception as e:
#         print(f"Error: {e}")
#         return None


async def is_adr_dead_or_null_or_unreal(check_adr: str) -> bool:
    check_adr = check_adr.lower()
    if len(check_adr) != 42 or check_adr == null_adr or check_adr == dead_adr:
        return True
    return False

#COMMON SECTION BEGIN ***
cmn_v2_fctr_min_abi_eth = '[{"constant":true,"inputs":[{"internalType":"address","name":"","type":"address"},{"internalType":"address","name":"","type":"address"}],"name":"getPair","outputs":[{"internalType":"address","name":"","type":"address"}],"payable":false,"stateMutability":"view","type":"function"}]'
cmn_v2_pair_min_abi = '[{"constant":true,"inputs":[],"name":"getReserves","outputs":[{"internalType":"uint112","name":"_reserve0","type":"uint112"},{"internalType":"uint112","name":"_reserve1","type":"uint112"},{"internalType":"uint32","name":"_blockTimestampLast","type":"uint32"}],"payable":false,"stateMutability":"view","type":"function"},{"inputs":[],"name":"token0","outputs":[{"internalType":"address","name":"","type":"address"}],"payable":false,"stateMutability":"view","type":"function"},{"inputs":[],"name":"token1","outputs":[{"internalType":"address","name":"","type":"address"}],"payable":false,"stateMutability":"view","type":"function"}]'
cmn_v3_fctr_min_abi_eth = '[{"inputs":[{"internalType":"address","name":"","type":"address"},{"internalType":"address","name":"","type":"address"},{"internalType":"uint24","name":"","type":"uint24"}],"name":"getPool","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"}]'
cmn_v3_pool_min_abi = '[{"inputs":[],"name":"liquidity","outputs":[{"internalType":"uint128","name":"","type":"uint128"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"slot0","outputs":[{"internalType":"uint160","name":"sqrtPriceX96","type":"uint160"},{"internalType":"int24","name":"tick","type":"int24"},{"internalType":"uint16","name":"observationIndex","type":"uint16"},{"internalType":"uint16","name":"observationCardinality","type":"uint16"},{"internalType":"uint16","name":"observationCardinalityNext","type":"uint16"},{"internalType":"uint8","name":"feeProtocol","type":"uint8"},{"internalType":"bool","name":"unlocked","type":"bool"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"token0","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"token1","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"tickSpacing","outputs":[{"internalType":"int24","name":"","type":"int24"}],"stateMutability":"view","type":"function"}]'
#COMMON SECTION END !!!
#ETH SECTION BEGIN ***
#uni_v1_fctr = "0xc0a47dFe034B400B47bDaD5FecDa2621de6c4d95"
uni_v2_fctr = "0x5c69bee701ef814a2b6a3edd4b1652cb9cc5aa6f"
uni_v3_fctr = "0x1F98431c8aD98523631AE4a59f267346ea31F984"
weth_cntr = "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"
usdt_eth_cntr = "0xdAC17F958D2ee523a2206206994597C13D831ec7"
#uni_v2_fctr_abi_eth = asyncio.run(get_contract_abi(uni_v2_fctr, "eth"))
uni_v2_fctr_abi_eth = cmn_v2_fctr_min_abi_eth
#uni_v3_fctr_abi_eth = asyncio.run(get_contract_abi(uni_v3_fctr, "eth"))
uni_v3_fctr_abi_eth = cmn_v3_fctr_min_abi_eth
#ETH SECTION END !!!
#BSC SECTION BEGIN ***
#uni_v1_fctr = "0xc0a47dFe034B400B47bDaD5FecDa2621de6c4d95"
pcake_v2_fctr = "0xcA143Ce32Fe78f1f7019d7d551a6402fC5350c73"
pcake_v3_fctr = "0x0BFbCF9fa4f9C56B0F40a671Ad40E0805A091865"
wbnb_cntr = "0xbb4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c"
usdt_bsc_cntr = "0x55d398326f99059fF775485246999027B3197955"
cake_bsc_cntr = "0x0E09FaBB73Bd3Ade0a17ECC321fD13a19e81cE82"
pcake_v2_fctr_abi_eth = cmn_v2_fctr_min_abi_eth
pcake_v3_fctr_abi_eth = cmn_v3_fctr_min_abi_eth
#BSC SECTION END !!!

async def a_get_pool_liqudity_for_contrtact(contract_address, provider):
    result: dict = {}
    
    provider_url = f"https://mainnet.infura.io/v3/{INFURA_API_KEY}"
    if provider == "bsc":
        provider_url = "https://bsc-dataseed.binance.org"
    try:
        web3 = Web3(Web3.HTTPProvider(provider_url))
        fixed_cntr_adr = web3.to_checksum_address(contract_address)
        #cntr_abi = await get_contract_abi(fixed_cntr_adr, provider) "constant":true,
        min_cntr_only_decimal_abi = '[{"inputs":[],"name":"decimals","outputs":[{"internalType":"uint8","name":"","type":"uint8"}],"payable":false,"stateMutability":"view","type":"function"}]'
        cntr_abi = min_cntr_only_decimal_abi

        cntr = web3.eth.contract(address=fixed_cntr_adr, abi=cntr_abi)
        decimal0 = cntr.functions.decimals().call()
    except Exception as e:
        print(f"Error: {e}")
        return {}
    
    base_coin_cntr = web3.to_checksum_address(weth_cntr)
    fixed_usdt_cntr = web3.to_checksum_address(usdt_eth_cntr)
    if provider == "bsc":
        base_coin_cntr = web3.to_checksum_address(wbnb_cntr)
        fixed_usdt_cntr = web3.to_checksum_address(usdt_bsc_cntr)
    fixed_cake_cntr = web3.to_checksum_address(cake_bsc_cntr)    
    #decimal1 = 18
    
    pool_fees = [500, 3000, 10000]
    if provider == "bsc":
        pool_fees = [100, 500, 2500, 10000]
    #tick_spaces = {500: 10, 3000: 60, 10000: 200}

    try:
        if provider == "eth":
            pair_provider = 'uniswapv2'
            fctr_cntr_v2 = web3.eth.contract(web3.to_checksum_address(uni_v2_fctr), abi=uni_v2_fctr_abi_eth)
            v2_pair_cntrs = [(base_coin_cntr, "eth", 18), (fixed_usdt_cntr, "usdt", 6)]
        elif provider == "bsc":
            pair_provider = 'pancakeswapv2'
            fctr_cntr_v2 = web3.eth.contract(web3.to_checksum_address(pcake_v2_fctr), abi=cmn_v2_fctr_min_abi_eth)
            v2_pair_cntrs = [(base_coin_cntr, "bnb", 18), (fixed_usdt_cntr, "bsc-usdt", 18), (fixed_cake_cntr, "cake", 18)]
        else:
            return {}
        result[pair_provider] = []
        
        for (token_base_cntr, token_base_name, token_base_decimal) in v2_pair_cntrs:
            v2_pool_adr = fctr_cntr_v2.functions.getPair(fixed_cntr_adr, token_base_cntr).call()
            if v2_pool_adr != null_adr:
                v2_pair_abi = cmn_v2_pair_min_abi
                # v2_pair_abi = await get_contract_abi(v2_pool_adr, provider)
                v2_pair_cntr = web3.eth.contract(v2_pool_adr, abi=v2_pair_abi)
                
                result[pair_provider].append({'type': 'v2','pool_adr': v2_pool_adr, \
                        'base_coin': token_base_name, \
                        'pool_fee': 0.25})
                
                reserves = v2_pair_cntr.functions.getReserves().call()
                
                cntr_token0 = v2_pair_cntr.functions.token0().call()
                if str(cntr_token0) == str(fixed_cntr_adr):
                    result[pair_provider][-1]['amount'] = round(float(reserves[1]) / (10**token_base_decimal),2)
                    result[pair_provider][-1]['price'] = \
                        round((float(reserves[1]) / (10**token_base_decimal)) / (float(reserves[0]) / (10**decimal0)), 5)
                else:
                    result[pair_provider][-1]['amount'] = round(float(reserves[0]) / (10**token_base_decimal),2)
                    result[pair_provider][-1]['price'] = \
                        round((float(reserves[0]) / (10**token_base_decimal)) / (float(reserves[1]) / (10**decimal0)), 5)
            
        if provider == "eth":
            pool_provider = 'uniswapv3'
            fctr_cntr_v3 = web3.eth.contract(web3.to_checksum_address(uni_v3_fctr), abi=uni_v3_fctr_abi_eth)
            v3_pool_cntrs = [(base_coin_cntr, "eth", 18), (fixed_usdt_cntr, "usdt", 6)]
        elif provider == "bsc":
            pool_provider = 'pancakeswapv3'
            fctr_cntr_v3 = web3.eth.contract(web3.to_checksum_address(pcake_v3_fctr), abi=cmn_v3_fctr_min_abi_eth)
            v3_pool_cntrs = [(base_coin_cntr, "bnb", 18), (fixed_usdt_cntr, "bsc-usdt", 18), (fixed_cake_cntr, "cake", 18)]
        else:
            return result
        
        result[pool_provider] = []
        for (token_base_cntr, token_base_name, token_base_decimal) in v3_pool_cntrs:
            for pool_fee in pool_fees:
                try:
                    v3_pool_adr = fctr_cntr_v3.functions.getPool(fixed_cntr_adr, token_base_cntr, pool_fee).call()
                    if v3_pool_adr == null_adr:
                        continue
                    v3_pool_abi = await get_contract_abi(v3_pool_adr, provider)
                    #v3_pool_abi = cmn_v3_pool_min_abi
                    v3_pool_cntr = web3.eth.contract(v3_pool_adr, abi=v3_pool_abi)

                    liquidity = int(v3_pool_cntr.functions.liquidity().call())
                    if liquidity == 0:
                        continue
                    sqrt_price_x96, current_tick, observation_index = v3_pool_cntr.functions.slot0().call()[:3]
                    # ticks = v3_pool_cntr.functions.ticks(current_tick).call()
                    tick_space = v3_pool_cntr.functions.tickSpacing().call()
                    
                    # Compute the current price
                    price = get_price_from_sqrt_price(float(sqrt_price_x96))
                    print(f"price: {price}")
                    # price = uniswap_v3_tick_to_price(current_tick)
                    # print(f"price: {price}")
                    price = round(price, 5)
                    
                    nearest_tick_below, nearest_tick_above = nearest_numbers_divisible_by_figure(current_tick, tick_space)
                    print(f"nearest_tick_below: {nearest_tick_below}, nearest_tick_above: {nearest_tick_above}")
                    # Compute the tick range near the current tick
                    
                    # Compute square roots of prices corresponding to the bottom and top ticks
                    sa = uniswap_v3_tick_to_price(nearest_tick_below // 2)
                    sb = uniswap_v3_tick_to_price(nearest_tick_above // 2)
                    sp = price ** 0.5

                    amount0 = liquidity * (sb - sp) / (sp * sb)
                    amount1 = liquidity * (sp - sa)
                    print(f"amount0: {amount0}, amount1: {amount1}")
                    
                    if amount0 < 0 or amount1 < 0:
                        nearest_tick_below = (np.floor(current_tick / tick_space)) * tick_space
                        nearest_tick_above = nearest_tick_below + tick_space
                        print(f"nearest_tick_below: {nearest_tick_below}, nearest_tick_above: {nearest_tick_above}")
                        
                        # amount0, amount1 = get_token_amounts(liquidity, sqrt_price_x96, nearest_tick_below, nearest_tick_above)
                        # print(f"amount0: {amount0}, amount1: {amount1}")
                        
                        sa = uniswap_v3_tick_to_price(nearest_tick_below // 2)
                        sb = uniswap_v3_tick_to_price(nearest_tick_above // 2)
                        sp = price ** 0.5

                        amount0 = liquidity * (sb - sp) / (sp * sb)
                        amount1 = liquidity * (sp - sa)
                        print(f"amount0: {amount0}, amount1: {amount1}")
                    
                    if abs(round(amount0, 3)) < 0.001 or abs(round(amount1, 3)) < 0.001:
                        continue
                    
                    amount0_ya = liquidity * (1 / price)
                    print(f"another try amount0: {amount0_ya}")
                    amount1_ya = amount0_ya * price
                    print(f"another try amount1: {amount1_ya}")
                    
                    cntr_token0 = v3_pool_cntr.functions.token0().call()
                    if str(cntr_token0) == str(fixed_cntr_adr):
                        amount_base_token_human = "{:.{}f}".format(amount1_ya / (10 ** token_base_decimal), token_base_decimal)
                    else:
                        amount_base_token_human = "{:.{}f}".format(amount0_ya / (10 ** token_base_decimal), token_base_decimal)
                        price = 1 / price
                    
                    print("Amount base Token:", amount_base_token_human)

                    result[pool_provider].append(
                        {'type': 'v3','pool_adr': v3_pool_adr,'pool_fee': round(float(pool_fee)/10000,2), \
                        'base_coin': token_base_name, \
                        'amount': round(float(amount_base_token_human),2), \
                        'price': round(float(price),5)})
                except Exception as e:
                    print(f"Error: {e}")
                    continue
    
    except Exception as e:
        print(f"Error: {e}")
        return {}
    
    return result

def liqudity_dict_to_html_table(data_dict):
    html = '<table style="border-collapse: collapse; width: 100%;">'
    html += '''
    <tr>
        <th style="border: 1px solid #dddddd; text-align: left; padding: 8px;">Платформа</th>
        <th style="border: 1px solid #dddddd; text-align: left; padding: 8px;">Основная монета</th>
        <th style="border: 1px solid #dddddd; text-align: left; padding: 8px;">Количество</th>
    </tr>
    '''

    for platform, entries in data_dict.items():
        row_span = len(entries)
        first_row = True
        for entry in entries:
            if first_row:
                html += f'''
                <tr>
                    <td style="border: 1px solid #dddddd; text-align: left; padding: 8px;" rowspan="{row_span}">{platform}</td>
                    <td style="border: 1px solid #dddddd; text-align: left; padding: 8px;">{entry["base_coin"]}</td>
                    <td style="border: 1px solid #dddddd; text-align: left; padding: 8px;">{entry["amount"]}</td>
                </tr>
                '''
                first_row = False
            else:
                html += f'''
                <tr>
                    <td style="border: 1px solid #dddddd; text-align: left; padding: 8px;">{entry["base_coin"]}</td>
                    <td style="border: 1px solid #dddddd; text-align: left; padding: 8px;">{entry["amount"]}</td>
                </tr>
                '''
    html += '</table>'
    return html


def holders_to_html_table(holders_list: list):
    html = '<table style="border-collapse: collapse; width: 100%;">'
    html += '''
    <tr>
        <th style="border: 1px solid #dddddd; text-align: left; padding: 8px;">Адрес</th>
        <th style="border: 1px solid #dddddd; text-align: left; padding: 8px;">Количество монет</th>
    </tr>
    '''
    # <th style="border: 1px solid #dddddd; text-align: left; padding: 8px;">Процент</th>
    for holder_item in holders_list:
        html += f'''
        <tr>
            <td style="border: 1px solid #dddddd; text-align: left; padding: 8px;">{holder_item['address']}</td>
            <td style="border: 1px solid #dddddd; text-align: left; padding: 8px;">{holder_item['balance']}</td>
        </tr>
        '''
    html += '</table>'
    return html