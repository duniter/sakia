"""
Ucoin public and private keys

@author: inso
"""

import base58
import base64
from pylibscrypt import scrypt
from libnacl.sign import Signer as NaclSigningKey


SEED_LENGTH = 32  # Length of the key
crypto_sign_BYTES = 64
SCRYPT_PARAMS = {'N': 4096,
                 'r': 16,
                 'p': 1
                 }

def _ensure_bytes(data):
    if isinstance(data, str):
        return bytes(data, 'utf-8')

    return data

class SigningKey(NaclSigningKey):
    def __init__(self, salt, password):
        salt = _ensure_bytes(salt)
        password = _ensure_bytes(password)
        seed = scrypt(password, salt,
                    SCRYPT_PARAMS['N'], SCRYPT_PARAMS['r'], SCRYPT_PARAMS['p'],
                    SEED_LENGTH)

        super().__init__(seed)
        self.pubkey = Base58Encoder.encode(self.vk)

class Base58Encoder(object):
    @staticmethod
    def encode(data):
        return base58.b58encode(data)

    @staticmethod
    def decode(data):
        return base58.b58decode(data)
