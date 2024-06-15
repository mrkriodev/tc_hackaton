from getopt import getopt
from brownie import accounts, web3 as web3_brownie
from brownie.network.account import Account
#from eth_account import Account
from .web3utils import get_contract_abi
from typing import Optional, List, Tuple
from web3.exceptions import ABIFunctionNotFound, MismatchedABI
from eth_utils.exceptions import ValidationError
from eth_typing import ChecksumAddress, Address

from brownie.project.compiler import install_solc
install_solc("0.8.24")


def test_transfer_for_scam(sc_adr_str, holder_adr_str, provider:str = "bsc") -> Optional[Tuple]:
    acc_one = accounts[1]
    acc_two = accounts[2]

    sc_adr_ca: ChecksumAddress = web3_brownie.to_checksum_address(sc_adr_str)
    holder_adr_ca: ChecksumAddress = web3_brownie.to_checksum_address(holder_adr_str)
    
    holder_adr = str(holder_adr_ca)

    min_sc_abi = '[{"inputs":[{"internalType":"address","name":"recipient","type":"address"},{"internalType":"uint256","name":"amount","type":"uint256"}],"name":"transfer","outputs":[{"internalType":"bool","name":"","type":"bool"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"Owner","type":"address"}],"name":"balanceOf","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"}]'
    # print(f"sc_asr={sc_adr_str}, provider={provider}")
    # contract_abi = get_contract_abi(sc_adr_str, provider)
    # print(contract_abi)
    web3cntr = None
    sc_abi = min_sc_abi # contract_abi
    while web3cntr is None:
        try:
            print("try to init contact by mini abi")
            web3cntr = web3_brownie.eth.contract(address=sc_adr_ca, abi=sc_abi)
            print("try get balanceOf")
            web3cntr.functions.balanceOf(holder_adr).call()
            # web3cntr.functions.transfer(acc_two.address, 1).call({'from': acc_one.address})
        except ABIFunctionNotFound as w3e:
            print(f"catch error {w3e}")
            web3cntr = None
            sc_abi = get_contract_abi(sc_adr_str, provider)
        except MismatchedABI as w3e:
            print(f"catch error {w3e}")
            web3cntr = None
            sc_abi = get_contract_abi(sc_adr_str, provider)
        except ValidationError as w3e:
            print(f"catch error {w3e}")
            web3cntr = None
            sc_abi = get_contract_abi(sc_adr_str, provider)
        except ValueError as w3e:
            print(f"catch error {w3e}")
            web3cntr = None
            sc_abi = get_contract_abi(sc_adr_str, provider)
        except Exception as e:
            print(f"catch error {e} of type({type(e)})")
            web3cntr =None
            sc_abi = get_contract_abi(sc_adr_str, provider)
            return

    # check eth balance of holder_adr
    print("try get holder balance")
    holder_balance = web3_brownie.eth.get_balance(holder_adr_ca) / 10 ** 18
    if holder_balance < 0.1:
        acc_one.transfer(to=Account(holder_adr), amount=web3_brownie.to_wei(0.1, "ether"))

    # send some tokens to acc_two grom one of holders
    holder_token_balance: int = abs(int(web3cntr.functions.balanceOf(holder_adr).call()) - 1)
    print(f"holder_token_balance = {holder_adr_ca} {holder_token_balance/10**18} tokens")
    for i in [100, 99, 98, 97, 96, 95, 94, 93, 92, 91, 90, 80, 10, 0]:  #, 70, 60, 50, 40, 30, 20, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1]:
        # try send tokens to acc_two
        stopped_i = i
        try:
            print(f"try send {i}% from one of holders = {holder_adr} = {int((float(i)/100)*holder_token_balance)/10**18} tokens")
            tx_hash = web3cntr.functions.transfer(acc_two.address, int((float(i)/100)*holder_token_balance)).transact(
                {'from': holder_adr})
            web3_brownie.eth.wait_for_transaction_receipt(tx_hash)
            print(f"tx_hash {web3_brownie.to_hex(tx_hash)}")
            break
        except Exception as e:
            print(f"catch error {e} of type({type(e)})")
            continue
    print(f"stopped_i = {stopped_i}")
    # if stopped_i != 100:
    #     return stopped_i
    #check balance of acc_two in tokens
    acc_two_balance: int = int(web3cntr.functions.balanceOf(acc_two.address).call())
    print(f"acc_two_balance {acc_two_balance/10**18} tokens")
    # check send and received balances
    result = 100
    if stopped_i != 100:
        result = round((acc_two_balance/(float(stopped_i)/100*holder_token_balance))*100, 2)
    else:
        result = round((float(acc_two_balance)/holder_token_balance)*100, 2)

    print(f"result: {stopped_i}@{100-result}")
    return stopped_i, (100-result)


def get_args(argv):
    try:
        opts, args = getopt(argv[1:], 's:u:', ['smart_contract=', 'unlock_adr='])
    except getopt.GetoptError:
        print("No necessary input arguments")
        return 101

    if len(opts) < 2:
        print("No necessary input arguments")
        return 101
    for option, argument in opts:
        if option == '-s':
            checking_smart_contract_adr = argument
        if option == '-u':
            adr_with_tokens_in_smart_contract = argument
    return checking_smart_contract_adr, adr_with_tokens_in_smart_contract

# checking_smart_contract_adr, adr_with_tokens_in_smart_contract = get_args(sys.argv)
#test_transfer_for_scam(checking_smart_contract_adr, adr_with_tokens_in_smart_contract)
def main():
    test_transfer_for_scam("0xd4123c5dacec3061162dc663ccee4eac2f414403", "0xbcaceb699c14856f59f3f5d85f63cf0dfd0cb9e4", "sibr")
