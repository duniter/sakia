'''
Ucoin public and private keys

@author: inso
'''

import base58
import base64
import scrypt
from nacl.signing import SigningKey as NaclSigningKey
from nacl.encoding import Base64Encoder


SEED_LENGTH = 32  # Length of the key
crypto_sign_BYTES = 64
SCRYPT_PARAMS = {'N': 4096,
                 'r': 16,
                 'p': 1
                 }


class SigningKey(NaclSigningKey):
    def __init__(self, salt, password):
        seed = scrypt.hash(password, salt,
                    SCRYPT_PARAMS['N'], SCRYPT_PARAMS['r'], SCRYPT_PARAMS['p'],
                    SEED_LENGTH)

        super().__init__(seed)
        self.pubkey = self.verify_key.encode(encoder=Base58Encoder)


class Base58Encoder(object):
    @staticmethod
    def encode(data):
        return base58.b58encode(data)

    @staticmethod
    def decode(data):
        return base58.b58decode(data)
