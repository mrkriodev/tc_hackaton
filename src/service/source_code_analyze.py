import logging
from typing import Optional
from contractdata.utils import get_contract_source_code
from slither.slither_proc import contract_source_code_analytic

async def sc_source_code_analyze(sc_address: str, provided_symbol:str, provider: str, session):
    try:
        contract_code = await get_contract_source_code(sc_address, provider)
        if contract_code is None or not contract_code.get('SourceCode'):
            return None
        
        # call compilation analytic
        source_code_analytic_data = await contract_source_code_analytic(sc_address, provider, contract_code)
        return source_code_analytic_data
        
    except RuntimeError as runtime_error:
        # await operation_aireq_dao.stmt_delete_ai_request_by_adr(sc_address)
        raise runtime_error
    except Exception as e:
        logging.error(F"Error! sc_source_code_analyze response error: {e}")
        raise RuntimeError(F"Error! sc_source_code_analyze response error: {e}")