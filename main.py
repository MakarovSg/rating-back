from fastapi import FastAPI, HTTPException
from web3 import Web3
import requests, json
import time
app = FastAPI()
ALCHEMY_BASE_URL = "https://eth-mainnet.g.alchemy.com/nft/v2/"
ALCHEMY_API_KEY = "key"
def fetch_all_nfts(base_url, page_size=100):
    items = []
    page = 0

    while True:
        params = {
            "page": page,
            "pageSize": page_size
        }        
        headers = {"Content-Type": "application/json"}
        response = requests.get(base_url, params=params, headers=headers)

        if response.status_code != 200:
            break
        
        data = response.json()["ownedNfts"]
        if not data:
            break
        items.extend(data)
        if len(data) < 100:
            break
        time.sleep(0.2) # 5 free requests per seconds on infura 
        page += 1

    return items

def get_provider():
    return Web3.HTTPProvider(f"https://eth-mainnet.g.alchemy.com/v2/{ALCHEMY_API_KEY}")
@app.get("/holds_gems/{address}")
async def has_bluechip(address: str):
    w3 = Web3(get_provider())
    collection_contract_addresses = [
        "0x57f1887a8bf19b14fc0df6fd9b2acc9af147ea85".lower(), # ENS
        "0xBC4CA0EdA7647A8aB7C2061c2E118A18a936f13D".lower(), # BAYC
        "0xb47e3cd837dDF8e4c57F05d70Ab865de6e193BBB".lower(), # Punks
        "0x60E4d786628Fea6478F785A6d7e704777c86a7c6".lower(), # MAYC
        "0xED5AF388653567Af2F388E6224dC7C4b3241C544".lower(), # Azuki
    ]
    if not w3.is_address(address):
        raise ValueError("Invalid Ethereum address")
    nft_api_url = f"{ALCHEMY_BASE_URL}{ALCHEMY_API_KEY}/getNFTs?owner={address}&withMetadata=false"
    nft_data = fetch_all_nfts(nft_api_url)
    if not w3.is_connected():
        return False
    for nft in nft_data:
        nft_contract_address = nft["contract"]["address"]
        if nft_contract_address.lower() in collection_contract_addresses:
            return {"holder": "true"}

    return {"holder": "false"}

@app.get("/balance/{address}")
async def get_balance(address: str):
    # Check if the address is a valid Ethereum address
    w3 = Web3(Web3.HTTPProvider(f"https://eth-mainnet.g.alchemy.com/v2/{ALCHEMY_API_KEY}"))

    if not is_valid_ethereum_address(address):
        raise HTTPException(status_code=400, detail="Invalid Ethereum address")

    
    balance_wei = int( w3.eth.get_balance(address))
    balance_eth = balance_wei / 10**18

    return {"address": address, "balance": balance_eth}


def is_valid_ethereum_address(address: str) -> bool:
    if not address.startswith("0x") or len(address) != 42:
        return False
    try:
        int(address[2:], 16)
    except ValueError:
        return False
    return True
