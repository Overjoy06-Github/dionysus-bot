from pathlib import Path
import json

ECONOMY_FILE = "data/economy.json"

def get_balance(user_id):
    with open(ECONOMY_FILE) as f:
        data = json.load(f)
        return data.get(str(user_id), {}).get("balance", 100)

def load_balances():
    try:
        with open("data/economy.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def update_balance(user_id, amount):
    with open(ECONOMY_FILE, "r+") as f:
        data = json.load(f)
        user_data = data.setdefault(str(user_id), {"balance": 100})
        user_data["balance"] += amount
        f.seek(0)
        json.dump(data, f, indent=4)
        f.truncate()
