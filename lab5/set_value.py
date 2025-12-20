import json
from pathlib import Path

from web3 import Web3
from web3.middleware import ExtraDataToPOAMiddleware


# ====== НАСТРОЙКИ ======
RPC_URL = "http://127.0.0.1:8545"

PRIVATE_KEY = "63deeafcf9da6961401391817ddd36594d20884447d87fa3bb3d391077634a39"

CONTRACT_NAME = "DoubleString"
ABI_PATH = f"{CONTRACT_NAME}_abi.json"

ADDRESS_PATH = "contract_address.txt"
INPUT_STRING = "hello world!"

GAS_LIMIT = 200_000
# =======================


def build_fee_fields(w3: Web3) -> dict:
    latest = w3.eth.get_block("latest")
    if "baseFeePerGas" in latest and latest["baseFeePerGas"] is not None:
        base_fee = int(latest["baseFeePerGas"])
        priority = w3.to_wei(1, "gwei")
        max_fee = base_fee * 2 + priority
        return {
            "maxPriorityFeePerGas": priority,
            "maxFeePerGas": max_fee,
        }
    return {"gasPrice": w3.eth.gas_price}


def main():
    w3 = Web3(Web3.HTTPProvider(RPC_URL, request_kwargs={"timeout": 10}))

    if not w3.is_connected():
        raise ConnectionError(f"Не удалось подключиться к RPC: {RPC_URL}")

    acct = w3.eth.account.from_key(PRIVATE_KEY)
    sender = w3.to_checksum_address(acct.address)

    abi = json.loads(Path(ABI_PATH).read_text(encoding="utf-8"))
    contract_address = Path(ADDRESS_PATH).read_text(encoding="utf-8").strip()
    contract_address = w3.to_checksum_address(contract_address)

    contract = w3.eth.contract(address=contract_address, abi=abi)

    # Проверяем, что в ABI есть setValue(string)
    if not hasattr(contract.functions, "setValue"):
        funcs = [x.get("name") for x in contract.abi if x.get("type") == "function"]
        raise AttributeError(f"В ABI нет функции setValue(). Доступные функции: {funcs}")

    nonce = w3.eth.get_transaction_count(sender)
    fee_fields = build_fee_fields(w3)

    tx = contract.functions.setValue(INPUT_STRING).build_transaction({
        "chainId": w3.eth.chain_id,
        "from": sender,
        "nonce": nonce,
        "gas": GAS_LIMIT,
        **fee_fields,
    })

    signed = acct.sign_transaction(tx)
    raw = getattr(signed, "raw_transaction", None) or getattr(signed, "rawTransaction")

    print("Отправка подписанной транзакции setValue(...)")
    tx_hash = w3.eth.send_raw_transaction(raw)
    tx_hash_hex = tx_hash.hex()
    print("TxHash:", tx_hash_hex)

    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    print("Receipt:")
    print("  status:", receipt.status)
    print("  blockNumber:", receipt.blockNumber)
    print("  gasUsed:", receipt.gasUsed)

    # Сохраним хеш (удобно для tx_info.py)
    Path("last_set_tx_hash.txt").write_text(tx_hash_hex, encoding="utf-8")
    print("Сохранено: last_set_tx_hash.txt")

    # (Опционально) прочитаем значение, если есть getValue()
    if hasattr(contract.functions, "getValue"):
        val = contract.functions.getValue().call()
        print("getValue():", val)


if __name__ == "__main__":
    main()
