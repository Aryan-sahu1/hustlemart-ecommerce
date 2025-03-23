import base64
import string
import random
import hashlib
from Crypto.Cipher import AES

IV = '@@@@&&&&####$$$$'
BLOCK_SIZE = 16

def generate_checksum(param_dict, merchant_key, salt=None):
    params_string = __get_param_string__(param_dict)
    salt = salt if salt else __id_generator__(4)
    final_string = '%s|%s' % (params_string, salt)

    hasher = hashlib.sha256(final_string.encode())
    hash_string = hasher.hexdigest()
    hash_string += salt

    return __encode__(hash_string, IV, merchant_key)

def generate_refund_checksum(param_dict, merchant_key, salt=None):
    for i in param_dict:
        if "|" in param_dict[i]:
            param_dict={}  # Invalid input
            exit()
    params_string = __get_param_string__(param_dict)
    salt = salt if salt else __id_generator__(4)
    final_string = '%s|%s' % (params_string, salt)

    hasher = hashlib.sha256(final_string.encode())
    hash_string = hasher.hexdigest()
    hash_string += salt

    return __encode__(hash_string, IV, merchant_key)

def generate_checksum_by_str(param_str, merchant_key, salt=None):
    params_string=param_str
    salt = salt if salt else __id_generator__(4)
    final_string = '%s|%s' % (params_string , salt)

    hasher = hashlib.sha256(final_string.encode())
    hash_string = hasher.hexdigest()
    hash_string += salt

    return __encode__(hash_string, IV, merchant_key)

def verify_checksum(param_dict, merchant_key, checksum):
    if 'CHECKSUMHASH' in param_dict:
        param_dict.pop('CHECKSUMHASH')

    paytm_hash = __decode__(checksum, IV, merchant_key)
    salt = paytm_hash[-4:]
    calculated_checksum = generate_checksum(param_dict, merchant_key, salt=salt)

    return calculated_checksum == checksum

def verify_checksum_by_str(param_str, merchant_key, checksum):
    paytm_hash = __decode__(checksum, IV, merchant_key)
    salt = paytm_hash[-4:]
    calculated_checksum = generate_checksum_by_str(param_str, merchant_key, salt=salt)

    return calculated_checksum == checksum

def __id_generator__(size=6, chars=string.ascii_uppercase + string.digits + string.ascii_lowercase):
    return ''.join(random.choice(chars) for _ in range(size))

def __get_param_string__(params):
    params_string = []
    for key in sorted(params.keys()):
        if ("REFUND" in params[key] or "|" in params[key]):
            respons_dict={}
            exit()
        value = params[key]
        params_string.append('' if value == 'null' else str(value))
    return '|'.join(params_string)

__pad__ = lambda s: s + (BLOCK_SIZE - len(s) % BLOCK_SIZE) * chr(BLOCK_SIZE - len(s) % BLOCK_SIZE)
__unpad__ = lambda s: s[0:-ord(s[-1])]

def __encode__(to_encode, iv, key):
    to_encode   = __pad__(to_encode)
    
    c = AES.new(key.encode('utf-8'), AES.MODE_CBC, iv.encode('utf-8'))
    encrypted_bytes = c.encrypt(to_encode.encode('utf-8'))
    encoded_string = base64.b64encode(encrypted_bytes)

    return encoded_string.decode("UTF-8")

def __decode__(to_decode, iv, key):
    decoded_bytes = base64.b64decode(to_decode)
    
    cipher = AES.new(key.encode('utf-8'), AES.MODE_CBC, iv.encode('utf-8'))
    decrypted_bytes = cipher.decrypt(decoded_bytes)

    # if isinstance(decrypted_bytes, bytes):
    if type(decrypted_bytes)==bytes:
        decrypted_bytes = decrypted_bytes.decode()
        
    return __unpad__(decrypted_bytes)

if __name__ == "__main__":
    params = {
        "MID": "mid",
        "ORDER_ID": "order_id",
        "CUST_ID": "cust_id",
        "TXN_AMOUNT": "1",
        "CHANNEL_ID": "WEB",
        "INDUSTRY_TYPE_ID": "Retail",
        "WEBSITE": "xxxxxxxxxxx"
    }

    print(verify_checksum(
        params, 'xxxxxxxxxxxxxxxx',
        "CD5ndX8VVjlzjWbbYoAtKQIlvtXPypQYOh0Fi2AUYKXZA5XSHiRF0FDj7vQu66S8MHx9NaDZ/uYm3WBOWHf+sDQAmTyxqUipA7i1nILlxrk="
    ))
