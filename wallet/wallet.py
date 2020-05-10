import os
from constants import *
import subprocess
import json
from dotenv import load_dotenv
from web3 import Web3
from web3.middleware import geth_poa_middleware
from web3.gas_strategies.time_based import medium_gas_price_strategy
from bit import wif_to_key, PrivateKeyTestnet
from bit.network import NetworkAPI
from eth_account import Account
from getpass import getpass

load_dotenv()

w3 = Web3(Web3.HTTPProvider("http://127.0.0.1:8545"))
w3.middleware_onion.inject(geth_poa_middleware, layer=0)
w3.eth.setGasPriceStrategy(medium_gas_price_strategy)

# Get environment variable containing a mnemonic, stored in a secure .env file, and save it to a variable.
mnemonic = os.getenv('MNEMONIC')

# Create a list of accounts associated with a particular coin and mnemonic, and select the number of accounts to be included in the list.
def derive_wallets(mnemonic, coin, number):  
    command = f"./derive -g --mnemonic ='{mnemonic}' --coin='{coin}' --cols=index,path,address,privkey,pubkeyhash,xprv,xpub --format=json"
    p = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True)
    (output, err) = p.communicate()
    p_status = p.wait()
    keys = json.loads(output)
    return keys

class coin:
    BTC = 'btc'
    ETH = 'eth'
    BTCTEST = 'btc-test'
    
# Generate a byte object given a coin and private key to an account.
def priv_key_to_account(coin, privkey):
    if coin == ETH:
        return Account.privateKeyToAccount(privkey)
    elif coin == BTCTEST:
        return PrivateKeyTestnet(privkey)
    
# Set up the transaction attributes based on the input of coin, byte object generated from the sender's private key in priv_key_to_account(), the recipient's account address, and the amount to send.
def create_tx(coin, account, to, amount):
    if coin == ETH:
        gasEstimate = w3.eth.estimateGas(
            {"from": account.address, "to": to, "value": amount}
        )
        return {
            "from": account.address,
            "to": to,
            "value": amount,
            "gasPrice": w3.eth.gasPrice,
            "gas": gasEstimate,
            "nonce": w3.eth.getTransactionCount(account.address)
        }    
    elif coin == BTCTEST:
        return PrivateKeyTestnet.prepare_transaction(account.address, [(to, amount, BTC)])
    
# Send the transaction. Take in the same parameters as above, run the above function, and sign the transaction. Then send the transaction through based on each coin's requirements.
def send_tx(coin, account, to, amount):
    tx = create_tx(coin, account, to, amount)
    signed_tx = account.sign_transaction(tx)
    if coin == ETH:
        result = w3.eth.sendRawTransaction(signed_tx.rawTransaction)
        print(result.hex())
        return result.hex()
    elif coin == BTCTEST:
        return NetworkAPI.broadcast_tx_testnet(signed_tx)