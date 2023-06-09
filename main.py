from fastapi import FastAPI, HTTPException
from web3 import Web3
import requests, os, time, datetime
from fastapi import FastAPI, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
import numpy as np

class CORSMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Authorization, Content-Type, Accept, Origin, User-Agent, Cache-Control, Keep-Alive, If-Modified-Since, X-Requested-With"
        return response

app = FastAPI()
app.add_middleware(CORSMiddleware)
ALCHEMY_BASE_URL = "https://eth-mainnet.g.alchemy.com/nft/v2/"
ALCHEMY_API_KEY = os.environ["ALCHEMY_API_KEY"]



def fetch_all_nfts(base_url, page_size=100):
    items = []
    page = 0

    params = {"page": page, "pageSize": page_size}
    headers = {"Content-Type": "application/json"}
    response = requests.get(base_url, params=params, headers=headers)
    if response.status_code != 200:
        return []

    data = response.json()["ownedNfts"]

    return data




async def get_age_score(address):
    w3 = Web3(get_provider())

    if not w3.is_address(address):
        return 0

    address = w3.to_checksum_address(address)
    start_block = 0
    end_block = w3.eth.block_number

    found_block = None

    # Binary search
    while start_block <= end_block:
        mid_block = (start_block + end_block) // 2
        balance = w3.eth.get_balance(address, block_identifier=mid_block)

        if balance > 0:
            found_block = mid_block
            end_block = mid_block - 1
        else:
            start_block = mid_block + 1

    if found_block is not None:
        block = w3.eth.get_block(found_block)
        timestamp = block.timestamp
        age = datetime.datetime.now() - datetime.datetime.fromtimestamp(timestamp)
        if age.days > 365:
            return 5
        elif age.days > 100:
            return 2
        return 0
    return 0



def get_provider():
    return Web3.HTTPProvider(f"https://eth-mainnet.g.alchemy.com/v2/{ALCHEMY_API_KEY}")


async def has_bluechip(address: str):
    w3 = Web3(get_provider())
    score = 0;
    collection_contract_addresses = {
        "0x57f1887a8bf19b14fc0df6fd9b2acc9af147ea85".lower(): 10,  # ENS
        "0xBC4CA0EdA7647A8aB7C2061c2E118A18a936f13D".lower(): 6,  # BAYC
        "0xb47e3cd837dDF8e4c57F05d70Ab865de6e193BBB".lower(): 7,  # Punks
        "0x60E4d786628Fea6478F785A6d7e704777c86a7c6".lower(): 4,  # MAYC
        "0xED5AF388653567Af2F388E6224dC7C4b3241C544".lower(): 4,  # Azuki
    }
    if not w3.is_address(address):
        raise ValueError("Invalid Ethereum address")
    nft_api_url = f"{ALCHEMY_BASE_URL}{ALCHEMY_API_KEY}/getNFTs?owner={address}&withMetadata=false"
    nft_data = fetch_all_nfts(nft_api_url)
    for nft in nft_data:
        nft_contract_address = nft["contract"]["address"]
        if nft_contract_address.lower() in collection_contract_addresses.keys():
            score += collection_contract_addresses.pop(nft_contract_address.lower())
            
    print(score)
    return False


@app.get("/rating/{address}")
async def get_score(address: str):
    # Check if the address is a valid Ethereum address
    w3 = Web3(
        Web3.HTTPProvider(f"https://eth-mainnet.g.alchemy.com/v2/{ALCHEMY_API_KEY}")
    )

    if not w3.is_address(address):
        raise HTTPException(status_code=400, detail="Invalid Ethereum address")

    balance_wei = int(w3.eth.get_balance(w3.to_checksum_address(address.lower())))
    balance_eth = balance_wei / 10**18

    rating = 7
    rating += await has_bluechip(address=address)
    rating += await get_age_score(address)
    if balance_eth > 1:
        rating += 1
    score = 1 / (1 + np.exp(-0.15 * (rating - 8)))
    response = {"rating": score}
    return response
