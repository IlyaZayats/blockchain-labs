from web3 import Web3

RPC_URL = "http://127.0.0.1:8545"
TX_HASH = "6829519bf168917a2415551576a6eb873ce3ac580d77d282032d3a59371e7b27"

def main():
    w3 = Web3(Web3.HTTPProvider(RPC_URL))
    txh = Web3.to_hex(hexstr=TX_HASH)

    tx = w3.eth.get_transaction(txh)
    receipt = w3.eth.get_transaction_receipt(txh)
    block = w3.eth.get_block(receipt.blockNumber)

    print("=== Transaction ===")
    print("hash:", tx["hash"].hex())
    print("from:", tx["from"])
    print("to:", tx["to"])
    print("nonce:", tx["nonce"])
    print("value (wei):", tx["value"])
    print("gas:", tx["gas"])
    print("maxFeePerGas:", tx.get("maxFeePerGas"))
    print("maxPriorityFeePerGas:", tx.get("maxPriorityFeePerGas"))

    print("\n=== Receipt ===")
    print("status:", receipt["status"])
    print("blockNumber:", receipt["blockNumber"])
    print("gasUsed:", receipt["gasUsed"])
    print("contractAddress:", receipt.get("contractAddress"))
    print("logs:", len(receipt["logs"]))

    print("\n=== Block ===")
    print("number:", block["number"])
    print("hash:", block["hash"].hex())
    print("timestamp:", block["timestamp"])
    print("miner:", block.get("miner"))
    print("txCount:", len(block["transactions"]))

if __name__ == "__main__":
    main()
