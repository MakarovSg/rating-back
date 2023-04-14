from fastapi import FastAPI, HTTPException
from web3 import Web3
import requests

app = FastAPI()
ALCHEMY_BASE_URL = "https://eth-mainnet.g.alchemy.com/nft/v2/"
ALCHEMY_API_KEY = "key"

@app.get("/nfts/{address}")
async def list_nfts(address: str):
    url = f"{ALCHEMY_BASE_URL}{ALCHEMY_API_KEY}/getNFTs?owner={address}&withMetadata=true&pageSize=100"
    headers = {"Content-Type": "application/json"}
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    result = response.json()["ownedNfts"]
    return {"nfts": result}

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
