from .runtime import Fernet, s


# authencation operations
def login(name, password):
    key = Fernet.generate_key()
    f = Fernet(key)
    token = f.encrypt(password)
    s.auth = (name, password)

def logout():
    s.close()
