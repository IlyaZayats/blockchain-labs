import json
from urllib.request import urlopen, Request
from urllib.parse import quote

BASE_URL = "https://blockstream.info/testnet/api"   # testnet

SAT_PER_BTC = 100_000_000

def get_balance_json(address: str) -> dict:
    url = f"{BASE_URL}/address/{quote(address)}"
    req = Request(url, headers={"User-Agent": "balance-script"})
    data = json.loads(urlopen(req, timeout=15).read().decode("utf-8"))

    chain = data["chain_stats"]
    mempool = data["mempool_stats"]

    confirmed = chain["funded_txo_sum"] - chain["spent_txo_sum"]
    mempool_delta = mempool["funded_txo_sum"] - mempool["spent_txo_sum"]
    total = confirmed + mempool_delta

    return {
        "address": address,
        "confirmed_sats": confirmed,
        "mempool_delta_sats": mempool_delta,
        "total_sats": total,
        "total_btc": total / SAT_PER_BTC,
    }

if __name__ == "__main__":
    addr = "tb1q0ttzh2s8xspr5rp0eckulehg4u9yada9mvptdh36ksh2kguqca0sw2gfr5"
    print(json.dumps(get_balance_json(addr), indent=2))