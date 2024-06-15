from dotenv import load_dotenv
import os
    
if os.path.exists(os.path.join(os.getcwd(), ".env")):
    load_dotenv(dotenv_path=os.path.join(os.getcwd(), ".env"),
                verbose=True)
elif os.path.exists(os.path.join(os.path.join(os.getcwd(), "src"), ".env")):
    load_dotenv(dotenv_path=os.path.join(os.path.join(os.getcwd(), "src"), ".env"),
                verbose=True)

AI_API_KEY = os.getenv("AI_API_KEY")
AI_API_ENDPOINT = os.getenv("AI_API_ENDPOINT")
ETHERSCAN_API_KEY = os.getenv("ETHERSCAN_API_KEY")
BSCSCAN_API_KEY = os.getenv("BSCSCAN_API_KEY")
TRONSCAN_API_KEY = os.getenv("TRONSCAN_API_KEY")
TOKENS_LIST_FILE_PATH=os.path.join(os.getcwd(), "coins_list.json")
   
DB_HOST = str(os.getenv('DB_HOST'))
DB_PORT = str(os.getenv('DB_PORT'))
DB_NAME = str(os.getenv('DB_NAME'))
DB_USER = str(os.getenv('DB_USER'))
DB_PASSWORD = str(os.getenv('DB_PASSWORD'))
DB_DRIVER = str(os.getenv('DB_DRIVER'))
DB_ASYNC_DRIVER = f"{os.getenv('DB_DRIVER')}+asyncpg"

GOOGLE_CSE_ID = str(os.getenv('GOOGLE_CSE_ID'))
GOOGLE_CSE_API_KEY = str(os.getenv('GOOGLE_CSE_API_KEY'))

INFURA_API_KEY = str(os.getenv('INFURA_API_KEY'))

IS_PROD = bool(os.getenv('PROD', False))