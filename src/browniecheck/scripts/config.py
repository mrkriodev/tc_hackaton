from dotenv import load_dotenv
import os

if os.path.exists(os.path.join(os.getcwd(), ".env")):
    load_dotenv(dotenv_path=os.path.join(os.getcwd(), ".env"),
                verbose=True)
elif os.path.exists(os.path.join(os.path.join(os.getcwd(), "src"), ".env")):
    load_dotenv(dotenv_path=os.path.join(os.path.join(os.getcwd(), "src"), ".env"),
                verbose=True)

BSCSCAN_API_KEY = os.getenv("BSCSCAN_API_KEY")
ETHERSCAN_API_KEY = os.getenv("ETHERSCAN_API_KEY")
