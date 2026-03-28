from cryptography.fernet import Fernet

KEY_FILE = "secret.key"

def generate_key():
    key = Fernet.generate_key()
    with open(KEY_FILE, "wb") as f:
        f.write(key)

def load_key():
    return open(KEY_FILE, "rb").read()

def encrypt_data(data):
    key = load_key()
    f = Fernet(key)
    return f.encrypt(data)

def decrypt_data(data):
    key = load_key()
    f = Fernet(key)
    return f.decrypt(data)