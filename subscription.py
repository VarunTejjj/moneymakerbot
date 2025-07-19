# subscription.py
import random, string, time

def generate_key():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))

def get_expiry():
    return int(time.time()) + 7 * 24 * 60 * 60
