import logging
from web3wrap.utils import a_get_pool_liqudity_for_contrtact

async def sc_liq_pool_analyze(sc_address: str, provider: str, session):
    try:
        #liquidty statistics
        if provider in ["eth", "bsc"]:
            liqudity_pool_info :dict = await a_get_pool_liqudity_for_contrtact(sc_address, provider)
    
        return liqudity_pool_info
    except RuntimeError as runtime_error:
        # await operation_aireq_dao.stmt_delete_ai_request_by_adr(sc_address)
        raise runtime_error
    except Exception as e:
        logging.error(F"Error! API  response error: {e}")
        raise RuntimeError(F"Error! API base_analyze_sc response error: {e}")