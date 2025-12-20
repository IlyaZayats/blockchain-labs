import json
from pathlib import Path

from web3 import Web3
from solcx import compile_standard, install_solc

#install_solc("0.8.0")

class ContractDeployer:
    def __init__(self, node_url: str, private_key: str, inject_poa: bool = True):
        self.node_url = node_url
        self.w3 = Web3(Web3.HTTPProvider(self.node_url, request_kwargs={"timeout": 10}))

        if not self.w3.is_connected():
            raise ConnectionError(f"Не удалось подключиться к ноде по адресу {self.node_url}")

        self.private_key = private_key
        self.account = self.w3.eth.account.from_key(self.private_key)
        self.from_address = self.w3.to_checksum_address(self.account.address)

        print("Успешное подключение к ноде Ethereum")
        print(f"   RPC: {self.node_url}")
        print(f"   Chain ID: {self.w3.eth.chain_id}")
        print(f"   Блок: {self.w3.eth.block_number}")
        print(f"   Отправитель: {self.from_address}")

    def compile_contract(
        self,
        contract_path: str,
        contract_name: str,
        save_artifacts: bool = True,
        artifacts_prefix: str = "contract",
    ):
        """
        Компилирует Solidity контракт через solcx.compile_standard
        (как в твоём примере).
        Возвращает: (abi, bytecode)
        """
        print(f"\nКомпиляция: {contract_path} (контракт: {contract_name}")

        path = Path(contract_path)
        if not path.exists():
            raise FileNotFoundError(f"Файл не найден: {contract_path}")

        source_code = path.read_text(encoding="utf-8")

        compile_settings = {
            "language": "Solidity",
            "sources": {
                path.name: {
                    "content": source_code
                }
            },
            "settings": {
                "outputSelection": {
                    "*": {
                        "*": ["abi", "metadata", "evm.bytecode", "evm.sourceMap"]
                    }
                }
            }
        }

        compiled = compile_standard(compile_settings, solc_version="0.8.0+commit.c7dfd78e.Windows.msvc")

        try:
            contract_data = compiled["contracts"][path.name][contract_name]
        except KeyError:
            available = list(compiled.get("contracts", {}).get(path.name, {}).keys())
            raise KeyError(
                f"Контракт '{contract_name}' не найден в {path.name}. "
                f"Доступные: {available}"
            )

        abi = contract_data["abi"]
        bytecode = contract_data["evm"]["bytecode"]["object"]

        print("Контракт успешно скомпилирован")
        print(f"   Функций/конструктора в ABI: {len(abi)}")
        print(f"   Длина bytecode: {len(bytecode)} символов")

        if save_artifacts:
            Path(f"{artifacts_prefix}_abi.json").write_text(
                json.dumps(abi, indent=2, ensure_ascii=False),
                encoding="utf-8"
            )
            Path(f"{artifacts_prefix}_bytecode.txt").write_text(bytecode, encoding="utf-8")
            Path(f"{artifacts_prefix}_compiled_full.json").write_text(
                json.dumps(compiled, indent=2, ensure_ascii=False),
                encoding="utf-8"
            )
            print(f"   ABI сохранён: {artifacts_prefix}_abi.json")
            print(f"   Bytecode сохранён: {artifacts_prefix}_bytecode.txt")

        return abi, bytecode

    def _build_fee_fields(self):
        """
        Возвращает словарь с fee полями:
        - если сеть поддерживает baseFeePerGas -> EIP-1559 (maxFeePerGas, maxPriorityFeePerGas)
        - иначе -> gasPrice
        """
        latest = self.w3.eth.get_block("latest")
        # EIP-1559 сети обычно имеют baseFeePerGas
        if "baseFeePerGas" in latest and latest["baseFeePerGas"] is not None:
            base_fee = int(latest["baseFeePerGas"])
            priority = self.w3.to_wei(1, "gwei")
            max_fee = base_fee * 2 + priority
            return {
                "maxPriorityFeePerGas": priority,
                "maxFeePerGas": max_fee,
            }
        else:
            return {
                "gasPrice": self.w3.eth.gas_price
            }

    def deploy_contract(self, abi, bytecode, constructor_args=None, gas_limit: int = 2_000_000):
        """
        Деплоит контракт. constructor_args — список аргументов конструктора (или None/[])
        """
        constructor_args = constructor_args or []

        print(f"\nДеплой контракта. Аргументы конструктора: {constructor_args}")

        Contract = self.w3.eth.contract(abi=abi, bytecode=bytecode)

        nonce = self.w3.eth.get_transaction_count(self.from_address)

        fee_fields = self._build_fee_fields()

        tx = Contract.constructor(*constructor_args).build_transaction({
            "chainId": self.w3.eth.chain_id,
            "from": self.from_address,
            "nonce": nonce,
            "gas": gas_limit,
            **fee_fields,
        })

        signed = self.w3.eth.account.sign_transaction(tx, self.private_key)

        # web3.py v6: signed.raw_transaction
        # web3.py v5: signed.rawTransaction
        raw = getattr(signed, "raw_transaction", None) or getattr(signed, "rawTransaction")

        print("Отправка транзакции деплоя...")
        tx_hash = self.w3.eth.send_raw_transaction(raw)
        tx_hash_hex = tx_hash.hex()
        print(f"   TxHash: {tx_hash_hex}")

        print("Ожидание подтверждения...")
        receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)

        contract_address = receipt.contractAddress
        print("Контракт успешно развернут!")
        print(f"   Адрес: {contract_address}")
        print(f"   Блок: {receipt.blockNumber}")
        print(f"   Gas использовано: {receipt.gasUsed}")
        print(f"   Статус: {receipt.status}")

        Path("contract_address.txt").write_text(contract_address, encoding="utf-8")
        Path("deploy_tx_hash.txt").write_text(tx_hash_hex, encoding="utf-8")
        Path("deploy_receipt.json").write_text(
            json.dumps(dict(receipt), indent=2, default=str, ensure_ascii=False),
            encoding="utf-8"
        )

        return contract_address, tx_hash_hex, receipt


def main():
    # ====== НАСТРОЙКИ ======
    NODE_URL = "http://127.0.0.1:8545"
    PRIVATE_KEY = "63deeafcf9da6961401391817ddd36594d20884447d87fa3bb3d391077634a39"
    CONTRACT_PATH = r"DoubleString.sol"
    CONTRACT_NAME = "DoubleString"

    # =======================

    print("=" * 60)
    print("Компиляция + Деплой смарт-контракта через solcx")
    print("=" * 60)

    deployer = ContractDeployer(
        node_url=NODE_URL,
        private_key=PRIVATE_KEY,
        inject_poa=True
    )

    abi, bytecode = deployer.compile_contract(
        contract_path=CONTRACT_PATH,
        contract_name=CONTRACT_NAME,
        save_artifacts=True,
        artifacts_prefix=CONTRACT_NAME
    )

    contract_address, tx_hash, receipt = deployer.deploy_contract(
        abi=abi,
        bytecode=bytecode,
        gas_limit=2_000_000
    )

    print("\nГотово.")
    print(f"Адрес контракта: {contract_address}")
    print(f"TxHash деплоя:  {tx_hash}")
    print(f"ABI:            {CONTRACT_NAME}_abi.json")
    print(f"Bytecode:       {CONTRACT_NAME}_bytecode.txt")
    print("Адрес:          contract_address.txt")


if __name__ == "__main__":
    main()