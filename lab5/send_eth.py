import json
from web3 import Web3
from eth_account import Account

RPC_URL = "http://127.0.0.1:8545"
KEY_FILE = "sender_account.json"

TO_ADDRESS = "0x73530b7245F5808091F18E54239eCf777Ab11cE1"
AMOUNT_ETH = 0.01

def build_fee_fields(w3: Web3) -> dict:
    latest = w3.eth.get_block("latest")
    base_fee = latest.get("baseFeePerGas")
    if base_fee is None:
        return {"gasPrice": w3.eth.gas_price}

    try:
        priority = w3.eth.max_priority_fee
    except Exception:
        priority = w3.to_wei(2, "gwei")

    max_fee = int(base_fee * 2 + priority)
    return {
        "type": 2,
        "maxPriorityFeePerGas": int(priority),
        "maxFeePerGas": max_fee,
    }

def main():
    w3 = Web3(Web3.HTTPProvider(RPC_URL))
    if not w3.is_connected():
        raise SystemExit(f"Cannot connect to {RPC_URL}")

    with open(KEY_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    pk = data["private_key"]
    acct = Account.from_key(pk)
    from_addr = acct.address

    to_addr = w3.to_checksum_address(TO_ADDRESS)
    value = w3.to_wei(AMOUNT_ETH, "ether")

    nonce = w3.eth.get_transaction_count(from_addr, "pending")
    chain_id = w3.eth.chain_id

    tx = {
        "chainId": chain_id,
        "nonce": nonce,
        "from": from_addr,
        "to": to_addr,
        "value": value,
    }

    tx["gas"] = w3.eth.estimate_gas(tx)

    tx.update(build_fee_fields(w3))

    signed = w3.eth.account.sign_transaction(tx, private_key=pk)
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)

    print("From:", from_addr)
    print("To  :", to_addr)
    print("TxHash:", tx_hash.hex())

    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    print("\n=== Receipt ===")
    print("status:", receipt.status)
    print("blockNumber:", receipt.blockNumber)
    print("gasUsed:", receipt.gasUsed)

    tx_info = w3.eth.get_transaction(tx_hash)
    block = w3.eth.get_block(receipt.blockNumber)

    print("\n=== Transaction ===")
    print("hash:", tx_info["hash"].hex())
    print("from:", tx_info["from"])
    print("to  :", tx_info["to"])
    print("value(wei):", int(tx_info["value"]))
    print("nonce:", int(tx_info["nonce"]))

    print("\n=== Block ===")
    print("number:", int(block["number"]))
    print("hash  :", block["hash"].hex())
    print("timestamp:", int(block["timestamp"]))
    print("txs_in_block:", len(block["transactions"]))

if __name__ == "__main__":
    main()