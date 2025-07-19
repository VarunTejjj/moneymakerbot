# subscription_store.py

import json
import time

SUBSCRIPTION_FILE = "subscriptions.json"

def load_subscriptions():
    try:
        with open(SUBSCRIPTION_FILE, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_subscriptions(subs):
    with open(SUBSCRIPTION_FILE, "w") as f:
        json.dump(subs, f)

def get_user_expiry(user_id: int):
    subs = load_subscriptions()
    return subs.get(str(user_id), 0)

def set_user_subscription(user_id: int, expiry_timestamp: int):
    subs = load_subscriptions()
    subs[str(user_id)] = expiry_timestamp
    save_subscriptions(subs)
