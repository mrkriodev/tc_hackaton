import logging
import re
from typing import Optional
from ai_analytic.deberta_adapter import opcodes_deberta_analyze, source_code_deberta_analyze
from ai_analytic.gigachain_adapter import source_code_gigachain_analyze, source_code_gigachain_analyze_by_funcs, ya_source_code_gigachain_analyze
from contractdata.utils import get_contract_source_code
from slither.slither_proc import move_open_braces_to_previous_line, source_code_to_opcodes

reBeforeTransferFrom = '(function beforeTransferFrom){1}\([^\)]*\)\s+([a-zA-Z]+\s+)*(returns \([^\)]*\)\s+)?\{([^\}]+[^\{]*)+'
_reBeforeTransferFrom = '(function _beforeTransferFrom){1}\([^\)]*\)\s+([a-zA-Z]+\s+)*(returns \([^\)]*\)\s+)?\{([^\}]+[^\{]*)+'
reForTransferFrom = '(function transferFrom){1}\([^\)]*\)\s+([a-zA-Z]+\s+)*(returns \([^\)]*\)\s+)?\{([^\}]+[^\{]*)+'
_reForTransferFrom = '(function _transferFrom){1}\([^\)]*\)\s+([a-zA-Z]+\s+)*(returns \([^\)]*\)\s+)?\{([^\}]+[^\{]*)+'
reForTransfer = '(function transfer){1}\([^\)]*\)\s+([a-zA-Z]+\s+)*(returns \([^\)]*\)\s+)?\{([^\}]+[^\{]*)+'
_reForTransfer = '(function _transfer){1}\([^\)]*\)\s+([a-zA-Z]+\s+)*(returns \([^\)]*\)\s+)?{([^\}]+[^\{]*)+'

# yaReForTransfer = r'function\s+transfer\([^)]*\)\s+.*?{.*?}'
yaReForTransfer = r'function\s+transfer\s*\(.*?\)\s*{.*?}'
yaReForTransferFrom = r'function\s+transferFrom\s*\(.*?\)\s*{.*?}'
yaReBeforeTransferFrom = r'function\s+beforeTransferFrom\s*\(.*?\)\s*{.*?}'
_yaReForTransfer = r'function\s+_transfer\s*\(.*?\)\s*{.*?}'
_yaReForTransferFrom = r'function\s+_transferFrom\s*\(.*?\)\s*{.*?}'
_yaReBeforeTransferFrom = r'function\s+_beforeTransferFrom\s*\(.*?\)\s*{.*?}'


def extractTransfer(allStr):
    '''
    функция, чтобы достать искомой части из source_code
    '''
    str_in_array = allStr.split(sep='}', maxsplit=-1)
    finalTransferFrom = str_in_array[0] + '}'
    for i in range(1, len(str_in_array)):
        if 'function' not in str_in_array[i]:
            finalTransferFrom += str_in_array[i]
            finalTransferFrom += '}'
        else:
            break
    return finalTransferFrom


async def extractFunctionFile(source_code: str, transRegex):
    '''
    функция для получения source_code транзакции и парсингом требуемой функции из него
    source_code - source_code из файла
    transRegex - регулярное выражения для этой функции
    '''
    receivedFunc = re.search(transRegex, source_code)
    if receivedFunc is not None:
        allStr = receivedFunc.group(0)
        tr = extractTransfer(allStr)
    else:
        tr = ''
    return tr


async def extract_longest_transfer_function(contract_text, func_regex):
    # Регулярное выражение для поиска определений функции transfer
    transfer_regex = re.compile(func_regex, re.DOTALL)
    # Найти все определения функции transfer
    transfer_functions = transfer_regex.findall(contract_text)

    # Найти самую длинную версию функции transfer
    if transfer_functions:
        longest_transfer_function = max(transfer_functions, key=len)
        return longest_transfer_function
    else:
        return ""


async def ai_sc_analyze(sc_address: str, provider: str, ai_adapter: str, session):
    try:
        contract_code = await get_contract_source_code(sc_address, provider)
        if contract_code is None or not contract_code.get('SourceCode'):
            return None
        
        src_code = "test"
        src_code : str = contract_code['SourceCode']
        
        # Removing single-line comments
        src_code_fixed_slashes = re.sub(r'\\n', '\n', src_code)
        solidity_code_no_single_line_comments = re.sub(r'//.*', '', src_code_fixed_slashes)
        solidity_code_no_comments = re.sub(r'/\*[\s\S]*?\*/', '', solidity_code_no_single_line_comments)
        solidity_code_no_comments_with_moved_braces = move_open_braces_to_previous_line(solidity_code_no_comments)
        # Removing multi-line comments
        solidity_code_no_comments = solidity_code_no_comments_with_moved_braces
        
        necessary_src_code_parts=[]
        # transfer_src_code = await extractFunctionFile(solidity_code_no_comments, reForTransfer)
        transfer_src_code = await extract_longest_transfer_function(solidity_code_no_comments, yaReForTransfer)
        # print(f"transfer_src_code={transfer_src_code}")
        if len(transfer_src_code) > 10:
            necessary_src_code_parts.append(transfer_src_code)
        
        # transferFrom_src_code = await extractFunctionFile(solidity_code_no_comments, reForTransferFrom)
        transferFrom_src_code = await extract_longest_transfer_function(solidity_code_no_comments, yaReForTransferFrom)
        # print(f"transferFrom_src_code={transferFrom_src_code}")
        if len(transfer_src_code) > 10:
            necessary_src_code_parts.append(transferFrom_src_code)
        
        # beforeTransferFrom_src_code = await extractFunctionFile(solidity_code_no_comments, reBeforeTransferFrom)
        beforeTransferFrom_src_code = await extract_longest_transfer_function(solidity_code_no_comments, yaReBeforeTransferFrom)
        if len(beforeTransferFrom_src_code) > 10:
            necessary_src_code_parts.append(beforeTransferFrom_src_code)
            
        # _tranfser_src_code = await extractFunctionFile(solidity_code_no_comments, _reForTransfer)
        _tranfser_src_code = await extract_longest_transfer_function(solidity_code_no_comments, _yaReForTransfer)
        # print(f"_tranfser_src_code={transferFrom_src_code}")
        if len(transfer_src_code) > 10:
            necessary_src_code_parts.append(_tranfser_src_code)
            
        # _tranfserFrom_src_code = await extractFunctionFile(solidity_code_no_comments, _reForTransferFrom)
        _tranfserFrom_src_code = await extract_longest_transfer_function(solidity_code_no_comments, _yaReForTransferFrom)
        # print(f"_tranfserFrom_src_code={transferFrom_src_code}")
        if len(transfer_src_code) > 10:
            necessary_src_code_parts.append(_tranfserFrom_src_code)
        
        # _beforeTransferFrom_src_code = await extractFunctionFile(solidity_code_no_comments, _reBeforeTransferFrom)
        _beforeTransferFrom_src_code = await extract_longest_transfer_function(solidity_code_no_comments, _yaReBeforeTransferFrom)
        if len(_beforeTransferFrom_src_code) > 10:
            necessary_src_code_parts.append(_beforeTransferFrom_src_code)
        
        if len(necessary_src_code_parts) < 1:
            return None
        if ai_adapter == "gigachain":    
            # source_code_ai_analytic_data = await source_code_gigachain_analyze("\n".join(necessary_src_code_parts))
            # source_code_ai_analytic_data = await source_code_gigachain_analyze_by_funcs(necessary_src_code_parts)
            source_code_ai_analytic_data = await ya_source_code_gigachain_analyze("\n".join(necessary_src_code_parts))
        elif ai_adapter == "deberta_src":
            source_code_ai_analytic_data = await source_code_deberta_analyze("\n".join(necessary_src_code_parts))
        
        ai_data = 0
        is_fraud = False
        if source_code_ai_analytic_data is not None and len(source_code_ai_analytic_data) > 0:
            ai_data = source_code_ai_analytic_data[0]
        if int(ai_data) > 0.44:
            is_fraud = True
        return {'ai_analyze_result': {'is_fraud': is_fraud, 'ai_data': ai_data}}
        
    except RuntimeError as runtime_error:
        # await operation_aireq_dao.stmt_delete_ai_request_by_adr(sc_address)
        raise runtime_error
    except Exception as e:
        logging.error(F"Error! sc_source_code_analyze response error: {e}")
        raise RuntimeError(F"Error! sc_source_code_analyze response error: {e}")
    

async def ai_opt_code_analyze(sc_address: str, provider: str, session):
    try:
        contract_code = await get_contract_source_code(sc_address, provider)
        if contract_code is None or not contract_code.get('SourceCode'):
            return None
        
        opcodes_text = await source_code_to_opcodes(sc_address, provider, contract_code['SourceCode'])
        if opcodes_text is None:
            return None
        
        opt_codes_ai_analytic_data = await opcodes_deberta_analyze(opcodes_text)
        return opt_codes_ai_analytic_data
        
    except RuntimeError as runtime_error:
        # await operation_aireq_dao.stmt_delete_ai_request_by_adr(sc_address)
        raise runtime_error
    except Exception as e:
        logging.error(F"Error! ai_opt_code_analyze response error: {e}")
        raise RuntimeError(F"Error! ai_opt_code_analyze response error: {e}")
