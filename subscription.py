# subscription.py

import random
import string
import time
from config import KEY_VALIDITY_DAYS

def generate_key():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))

def get_expiry():
    return int(time.time()) + KEY_VALIDITY_DAYS * 24 * 60 * 60
