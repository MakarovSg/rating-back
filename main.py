from fastapi import FastAPI, HTTPException
from web3 import Web3
import requests, json

app = FastAPI()
ALCHEMY_BASE_URL = "https://eth-mainnet.g.alchemy.com/nft/v2/"
ALCHEMY_API_KEY = "key"

def get_provider():
    return Web3.HTTPProvider(f"https://eth-mainnet.g.alchemy.com/v2/{ALCHEMY_API_KEY}")
@app.get("/holds_ens/{address}")
async def has_ens(address: str):
    w3 = Web3(get_provider())
    collection_contract_address = "0x57f1887a8bf19b14fc0df6fd9b2acc9af147ea85"
    if not w3.is_address(address):
        raise ValueError("Invalid Ethereum address")
    nft_api_url = f"{ALCHEMY_BASE_URL}{ALCHEMY_API_KEY}/getNFTs?owner={address}&withMetadata=true&pageSize=1000"
    headers = {"Content-Type": "application/json"}
    response = requests.get(nft_api_url, headers=headers)
    response.raise_for_status()
    nft_data = response.json()["ownedNfts"]
    if not w3.is_connected():
        return False

    print(nft_data)

    for nft in nft_data:
        nft_contract_address = nft["contract"]["address"]

        if nft_contract_address.lower() == collection_contract_address.lower():
            nft_token_id = nft["id"]["tokenId"]
            erc721_abi = json.loads('[{"constant":true,"inputs":[{"name":"tokenId","type":"uint256"},{"name":"owner","type":"address"}],"name":"exists","outputs":[{"name":"","type":"bool"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":true,"inputs":[{"name":"tokenId","type":"uint256"}],"name":"ownerOf","outputs":[{"name":"","type":"address"}],"payable":false,"stateMutability":"view","type":"function"}]')
            erc721_contract = w3.eth.contract(address=Web3.to_checksum_address(nft_contract_address), abi=erc721_abi)
            nft_owner = erc721_contract.functions.ownerOf(int(nft_token_id, 16)).call()

            if nft_owner.lower() == address.lower():
                return {"ENS": "true"}

    return {"ENS": "false"}

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
