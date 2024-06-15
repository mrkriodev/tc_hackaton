import logging
from fastapi import FastAPI
#from fastapi.middleware.cors import CORSMiddleware
import uvicorn

import sys
import os
sys.path.append(os.getcwd())

from src.service.router import main_api_service_router
# from src.gpt.router import gpt_api_service_router
from src.config import IS_PROD


app = FastAPI(
    title="Smart Contract analyzer",
    version="1.0.0",
    docs_url="/mydocs",  # Путь для Swagger UI
)
logging.basicConfig(level=logging.DEBUG)

# app.include_router(gpt_api_service_router)
app.include_router(main_api_service_router)

if __name__ == '__main__':
    if IS_PROD:
        uvicorn.run(app, host='0.0.0.0', port=8082)
    else:
        uvicorn.run(app, host='127.0.0.1', port=8082)