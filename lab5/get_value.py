import json
from pathlib import Path
from web3 import Web3
from web3.middleware import ExtraDataToPOAMiddleware


RPC_URL = "http://localhost:8545"
CONTRACT_NAME = "DoubleString"
ABI_PATH = f"{CONTRACT_NAME}_abi.json"
ADDRESS_PATH = "contract_address.txt"


def pick_getter_function(contract):
    candidates = ["getValue", "retrieve", "get", "value"]
    for name in candidates:
        if hasattr(contract.functions, name):
            return getattr(contract.functions, name)

    funcs = []
    for item in contract.abi:
        if item.get("type") == "function":
            funcs.append(item.get("name"))
    raise AttributeError(
        "Не нашёл getter-функцию среди getValue/retrieve/get/value.\n"
        f"Функции в ABI: {funcs}"
    )


def main():
    w3 = Web3(Web3.HTTPProvider(RPC_URL))
    w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)

    if not w3.is_connected():
        raise ConnectionError(f"Не удалось подключиться к ноде: {RPC_URL}")

    abi = json.loads(Path(ABI_PATH).read_text(encoding="utf-8"))
    contract_address = Path(ADDRESS_PATH).read_text(encoding="utf-8").strip()
    contract_address = w3.to_checksum_address(contract_address)

    contract = w3.eth.contract(address=contract_address, abi=abi)

    getter = pick_getter_function(contract)
    value = getter().call()

    print("=== Contract Value ===")
    print("Contract:", contract_address)
    print("Getter:", getter.fn_name)
    print("Value:", value)


if __name__ == "__main__":
    main()