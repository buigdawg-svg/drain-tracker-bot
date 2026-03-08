import requests
import csv
import os
from datetime import datetime

ETHERSCAN_KEY = "BT8XVVVD419Y23EXCAWDDNT83YBH3KZF2W"
DISCORD_WEBHOOK = "https://discord.com/api/webhooks/1480314603459051520/1c-chZP3-0XY9PE2lO_G6pE3255jTGiFNbHvbq0s0LO1Sp0xLl28dX4ayIP0qlUGZG5U"

VALUE_THRESHOLD = 50

PROTOCOLS = [
"0x5C69bEe701ef814a2B6a3EDD4B1652CB9cc5aA6f",
"0xE592427A0AEce92De3Edee1F18E0157C05861564",
"0x7BeA39867e4169DBe237d55C8242a8f2fcDcc387",
"0xbEbc44782C7dB0a1A60Cb6Fe97d0b483032FF1C7",
"0x3d9819210A31b4961b30EF54bE2aeD79B9c9Cd3B",
"0x35d1b3f3d7966a1dfe207aa4514c12a259a0492b"
]

TORNADO = [
"0xd90e2f925da726b50c4ed8d0fb90ad053324f31b",
"0x47ce0c6eD5dE41cD6d1Ff6E15e6F6b6F4fC3bC6A",
"0x910Cbd523D972eb0a6f4cE7ab882C9eF3fD7A0c8"
]

FILE = "daily_drains.csv"


def log_tx(tx, value):
    with open(FILE, "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([tx, value])


def scan(address):

    url = f"https://api.etherscan.io/api?module=account&action=txlist&address={address}&sort=desc&apikey={ETHERSCAN_KEY}"

    r = requests.get(url).json()

    if r["status"] != "1":
        return

    for tx in r["result"][:5]:

        value = int(tx["value"]) / 1e18

        if value >= VALUE_THRESHOLD:
            log_tx(tx["hash"], value)


def send_discord(msg):

    requests.post(
        DISCORD_WEBHOOK,
        json={"content": msg}
    )


def generate_report():

    if not os.path.exists(FILE):
        return

    total = 0
    count = 0

    with open(FILE) as f:

        reader = csv.reader(f)

        for row in reader:
            count += 1
            total += float(row[1])

    msg = f"""
🚨 DAILY DRAIN REPORT

Transactions: {count}
Total Drained: ${total:,.2f}

Generated: {datetime.utcnow()}
"""

    send_discord(msg)

    os.remove(FILE)


def main():

    for addr in PROTOCOLS:
        scan(addr)

    for addr in TORNADO:
        scan(addr)

    now = datetime.utcnow()

    if now.hour == 22 and now.minute < 5:
        generate_report()


main()
