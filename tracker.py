import requests
import os
import datetime

ETHERSCAN_API = os.getenv("BT8XVVVD419Y23EXCAWDDNT83YBH3KZF2W")
DISCORD_WEBHOOK = os.getenv("https://discord.com/api/webhooks/1480314603459051520/1c-chZP3-0XY9PE2lO_G6pE3255jTGiFNbHvbq0s0LO1Sp0xLl28dX4ayIP0qlUGZG5U")

ETH_THRESHOLD = 50
DATA_FILE = "drains_today.txt"
SEEN_FILE = "seen_txids.txt"

BLOCK_LOOKBACK = 10


WATCHED_PROTOCOLS = {
"Uniswap V3 Router":"0xE592427A0AEce92De3Edee1F18E0157C05861564",
"Uniswap Universal Router":"0xEf1c6E67703c7BD7107eed8303Fbe6EC2554BF6B",
"Aave V3 Pool":"0x87870Bca3F3fD6335C3F4ce8392D69350B4Fa4E2",
"Curve Router":"0x99a58482bd75cbab83b27ec03ca68ff489b5788f",
"MakerDAO Proxy":"0xC2aDdA861F89bBB333c90c492cB837741916A225",
"1inch Router":"0x1111111254EEB25477B68fb85Ed929f73A960582",
"Balancer Vault":"0xBA12222222228d8Ba445958a75a0704d566BF2C8",
"SushiSwap Router":"0xd9e1cE17f2641F24aE83637ab66a2CCA9C378B9F",
"Lido Staking":"0xae7ab96520DE3A18E5e111B5EaAb095312D7fE84",
"Compound Comptroller":"0x3d9819210A31b4961b30EF54bE2aeD79B9c9Cd3B",
"Yearn Vault":"0x19D3364A399d251E894aC732651be8B0E4e85001",
"RocketPool Deposit":"0x1Cc9cF5586522c6F483E84A19c3C2B0B6d0271c4",
"dYdX":"0x1e0447b19bb6ecfdae1e4ae1694b0c3659614e4e",
"Pendle Router":"0x888888888889758F76e7103c6CbF23ABbF58F946",
"GMX Router":"0xaBBc5F99639c9B6bCb58544DdF04efa6802F4064",
"OpenSea Seaport":"0x00000000000000adc04c56bf30ac9d3c0aaf14dc",
"Blur Exchange":"0x000000000000Ad05Ccc4F10045630fb830B95127",
"MetaMask Swap Router":"0x881D40237659C251811CEC9c364ef91dC08D300C",
"0x Exchange Proxy":"0xDef1C0ded9bec7F1a1670819833240f027b25EfF",
"Paraswap Augustus":"0xDEF171Fe48CF0115B1d80b88dc8eAB59176FEe57",
"KyberSwap Router":"0x9AAb3f75489902f3a48495025729a0AF77d4b11e",
"CowSwap":"0x9008d19f58aabd9ed0d60971565aa8510560ab41"
}


TORNADO_ADDRESSES = {
"Tornado 100ETH":"0x910Cbd523D972eb0a6f4CAe4618Ad62622b39DbF",
"Tornado 10ETH":"0x47CE0C6eD5a2b1C9b2c5eF1B3c3e7C1a6f1cBaE8",
"Tornado 1ETH":"0x12D66f87A6bF6f5eC69FBB9f7dA1B6F62d2fA5b1"
}


def load_seen():
    if not os.path.exists(SEEN_FILE):
        return set()

    with open(SEEN_FILE) as f:
        return set(line.strip() for line in f)


def save_seen(txid):
    with open(SEEN_FILE,"a") as f:
        f.write(txid+"\n")


def get_latest_block():

    url=f"https://api.etherscan.io/v2/api?chainid=1&module=proxy&action=eth_blockNumber&apikey={ETHERSCAN_API}"

    r=requests.get(url).json()

    return int(r["result"],16)


def get_block_txs(block):

    tag=hex(block)

    url=f"https://api.etherscan.io/v2/api?chainid=1&module=proxy&action=eth_getBlockByNumber&tag={tag}&boolean=true&apikey={ETHERSCAN_API}"

    r=requests.get(url).json()

    return r["result"]["transactions"]


def eth_from_wei(v):
    return int(v,16)/10**18


def detect_protocol(addr):

    for name,a in WATCHED_PROTOCOLS.items():
        if addr and addr.lower()==a.lower():
            return name

    for name,a in TORNADO_ADDRESSES.items():
        if addr and addr.lower()==a.lower():
            return name

    return "Unknown"


def record(wallet,protocol,amount,tx):

    with open(DATA_FILE,"a") as f:
        f.write(f"{wallet}|{protocol}|{amount}|{tx}\n")


def send_discord(msg):

    if DISCORD_WEBHOOK:
        requests.post(DISCORD_WEBHOOK,json={"content":msg})


def scan_blocks():

    latest=get_latest_block()

    seen=load_seen()

    for block in range(latest-BLOCK_LOOKBACK,latest+1):

        txs=get_block_txs(block)

        for tx in txs:

            txid=tx["hash"]

            if txid in seen:
                continue

            value=eth_from_wei(tx["value"])

            wallet=tx["from"]

            to_addr=tx["to"]

            protocol=detect_protocol(to_addr)

            if value>=ETH_THRESHOLD or protocol!="Unknown":

                link=f"https://etherscan.io/tx/{txid}"

                record(wallet,protocol,value,link)

                save_seen(txid)


def send_report():

    if not os.path.exists(DATA_FILE):
        return

    drains=[]

    with open(DATA_FILE) as f:

        for line in f:

            w,p,a,t=line.strip().split("|")

            drains.append((w,p,float(a),t))

    if not drains:
        return

    total=sum(x[2] for x in drains)

    biggest=max(drains,key=lambda x:x[2])

    msg="📊 Daily Drain Report\n\n"

    msg+=f"Total ETH moved: {total:.2f}\n"

    msg+=f"Events: {len(drains)}\n\n"

    msg+="🔥 Biggest Event\n"

    msg+=f"Wallet: {biggest[0]}\n"

    msg+=f"Protocol: {biggest[1]}\n"

    msg+=f"Amount: {biggest[2]} ETH\n"

    msg+=f"{biggest[3]}\n\n"

    msg+="Top Events\n"

    for d in sorted(drains,key=lambda x:x[2],reverse=True)[:7]:

        msg+=f"{d[2]} ETH — {d[1]} — {d[3]}\n"

    send_discord(msg)

    os.remove(DATA_FILE)


def main():

    now=datetime.datetime.utcnow()

    scan_blocks()

    if now.hour==22 and now.minute<5:

        send_report()


if __name__=="__main__":

    main()
