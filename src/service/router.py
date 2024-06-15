import asyncio
from os import name
from fastapi import APIRouter, HTTPException, Query, Response, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from coingeko.coingeko_api import download_token_common_info, download_token_social_info, get_token_id
from contractdata.utils import get_contract_name
from google.search import search_for_links
from service.ai_analyze import ai_opt_code_analyze, ai_sc_analyze
from service.analyze_liq_pool import sc_liq_pool_analyze
from service.transfer_analyze import sc_transfer_analyze

from .schemas import AnalyzeRequest, PostAnalyzeRequest, QueryParams
from .baseanalyze import sc_base_analyze
from .source_code_analyze import sc_source_code_analyze

from src.core.driver import get_async_session
from src.exceptions import NoContractError, ProcessingError

main_api_service_router = APIRouter(
    prefix="/api",
    tags=["Smart contract processing"])

liquidity_pool_semaphore = asyncio.Semaphore(4)


@main_api_service_router.post('/base_analyze_sc')
async def api_sc_analytic_base_info(request_data: PostAnalyzeRequest, 
                                    session: AsyncSession = Depends(get_async_session)):
    try:
        #token_sc_adr = eoa_address.lower()
        token_sc_adr = request_data.sc_address.lower()
        _symbol = request_data.symbol.lower()
        _provider = request_data.provider
             
        print(f"api_sc_analytic_base_info new request: {token_sc_adr} with symbol {_symbol}")
        analyze_result_json = await sc_base_analyze(token_sc_adr, _symbol, _provider, session)
        if analyze_result_json is None:
            raise HTTPException(status_code=404, detail='Analysis result not found')

        return JSONResponse(content=analyze_result_json)
    except NoContractError as e:
        raise HTTPException(status_code=204, detail=f"{e.message}")
    except ProcessingError as e:
        raise HTTPException(status_code=429, detail=f"Request already in progress. {e.message}")
    except ValueError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    

@main_api_service_router.post('/analyze_liquidity_pool_sc')
async def api_analyze_liquidity_pool_sc(request_data: PostAnalyzeRequest, 
                                        session: AsyncSession = Depends(get_async_session)):
    print(f"senaphore free positions:{liquidity_pool_semaphore._value}")
    if liquidity_pool_semaphore.locked():
        return JSONResponse(status_code=202, content={"message": "Another request is being processed. Please wait."})
    
    async with liquidity_pool_semaphore:
        try:
            token_sc_adr = request_data.sc_address.lower()
            _provider = request_data.provider

            print(f"api_analyze_liquidity_pool_sc new request: {token_sc_adr}")

            analyze_result_json = await sc_liq_pool_analyze(token_sc_adr, _provider, session)
            if analyze_result_json is None:
                raise HTTPException(status_code=404, detail='Analysis result not found')
            return JSONResponse(analyze_result_json)
        except ProcessingError as e:
            raise HTTPException(status_code=429, detail=f"Request already in progress. {e.message}")
        except ValueError as e:
            raise HTTPException(status_code=403, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))


@main_api_service_router.post('/source_code_analyze_sc')
async def api_analytic_sc_source_code(request_data: PostAnalyzeRequest, 
                                      session: AsyncSession = Depends(get_async_session)):
    try:
        token_sc_adr = request_data.sc_address.lower()
        _symbol = request_data.symbol.lower()
        _provider = request_data.provider
        
        print(f"api_analytic_sc_source_code new request: {token_sc_adr} with symbol {_symbol}")

        analyze_result_json = await sc_source_code_analyze(token_sc_adr, _symbol, _provider, session)
        if analyze_result_json is None:
            raise HTTPException(status_code=404, detail='Analysis result not found')
        
        keys_to_include = ['has_error', 'enriched_erros_data_output', 'not_compiled']
        return JSONResponse(content={key: analyze_result_json[key] for key in keys_to_include if key in analyze_result_json})
    except ProcessingError as e:
        raise HTTPException(status_code=429, detail=f"Request already in progress. {e.message}")
    except ValueError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    

@main_api_service_router.post('/ai_gigachain_sc_analytic')
async def api_ai_gigachain_sc_analytic(request_data: PostAnalyzeRequest, 
                                      session: AsyncSession = Depends(get_async_session)):
    try:
        token_sc_adr = request_data.sc_address.lower()
        _symbol = request_data.symbol.lower()
        _provider = request_data.provider
             
        print(f"api_ai_gigachain_sc_analytic new request: {token_sc_adr} with symbol {_symbol}")

        transfer_result_json = await ai_sc_analyze(token_sc_adr, _provider, "gigachain", session)
        if transfer_result_json is None:
            raise HTTPException(status_code=404, detail='Analysis result not found')
        return JSONResponse(content=transfer_result_json)
    except ProcessingError as e:
        raise HTTPException(status_code=429, detail=f"Request already in progress. {e.message}")
    except ValueError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    

@main_api_service_router.post('/ai_deberta_src_sc_analytic')
async def api_ai_deberta_src_sc_analytic(request_data: PostAnalyzeRequest, 
                                      session: AsyncSession = Depends(get_async_session)):
    try:
        token_sc_adr = request_data.sc_address.lower()
        _symbol = request_data.symbol.lower()
        _provider = request_data.provider
        
        print(f"api_ai_deberta_src_sc_analytic new request: {token_sc_adr} with symbol {_symbol}")

        transfer_result_json = await ai_sc_analyze(token_sc_adr, _provider, "deberta_src", session)
        if transfer_result_json is None:
            raise HTTPException(status_code=404, detail='Analysis result not found')
        
        return JSONResponse(content=transfer_result_json)
    except ProcessingError as e:
        raise HTTPException(status_code=429, detail=f"Request already in progress. {e.message}")
    except ValueError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    

# @main_api_service_router.post('/ai_deberta_sc_opcodes_analytic')
# async def api_ai_deberta_sc_opcodes_analytic(request_data: PostAnalyzeRequest, 
#                                       session: AsyncSession = Depends(get_async_session)):
#     try:
#         token_sc_adr = request_data.sc_address.lower()
#         _symbol = request_data.symbol.lower()
#         _provider = request_data.provider
        
#         print(f"api_ai_deberta_sc_opcodes_analytic new request: {token_sc_adr} with symbol {_symbol}")

#         transfer_result_json = await ai_opt_code_analyze(token_sc_adr, _provider, session)
#         if transfer_result_json is None:
#             raise HTTPException(status_code=404, detail='Analysis result not found')
        
#         return JSONResponse(content=transfer_result_json)
#     except ProcessingError as e:
#         raise HTTPException(status_code=429, detail=f"Request already in progress. {e.message}")
#     except ValueError as e:
#         raise HTTPException(status_code=403, detail=str(e))
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))


@main_api_service_router.post('/transfer_analyze_sc')
async def api_transfer_analyze_sc(request_data: PostAnalyzeRequest, 
                                  session: AsyncSession = Depends(get_async_session)):
    try:
        token_sc_adr = request_data.sc_address.lower()
        _symbol = request_data.symbol.lower()
        _provider = request_data.provider
             
        print(f"api_transfer_analyze_sc new request: {token_sc_adr} with symbol {_symbol}")

        transfer_result_json = await sc_transfer_analyze(token_sc_adr, _provider, session)
        if transfer_result_json is None:
            raise HTTPException(status_code=404, detail='Analysis result not found')
        
        return JSONResponse(content=transfer_result_json)
    except ProcessingError as e:
        raise HTTPException(status_code=429, detail=f"Request already in progress. {e.message}")
    except ValueError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    

@main_api_service_router.post('/get_social_info_about_sc')
async def api_get_socail_info_about_sc(request_data: PostAnalyzeRequest, 
                                             session: AsyncSession = Depends(get_async_session)):
    try:
        token_sc_adr = request_data.sc_address.lower()
        token_id_str = request_data.symbol.lower()
        _provider = request_data.provider
        
        info_dict = await download_token_social_info(token_id_str)
        if bool(info_dict):
            return JSONResponse(content=info_dict)
        else:
            return JSONResponse(content = {"detail": "social info not found"}, status_code=400)
    except ProcessingError as e:
        raise HTTPException(status_code=429, detail=f"Request already in progress. {e.message}")
    except ValueError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
#coingeko info
        
        # if _token_id is not None:
        #     price_history = await download_price_history(_token_id)
        #     if len(price_history) > 2:
        #         price_summary = await analyze_price_movement(price_history)
        #         html_report = insert_str_into_html(html_report, "<h2>Аналитика цены</h2>", ins_str_is_html=True)
        #         html_report = insert_str_into_html(html_report, price_summary, ins_str_is_html=False)
        #         token_plot = await token_price_plot(price_history)
        #         html_report = await insert_figure_into_html(html_report, token_plot)    
        #         # plt.savefig('temp_plot.png', format='png')
        
        #     social_info_dict = await download_token_social_info(_token_id)
        #     if bool(social_info_dict):
        #         html_report = await dict_insert_to_html(html_report, social_info_dict)