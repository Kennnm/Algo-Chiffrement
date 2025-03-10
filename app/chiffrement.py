import base64
import json
import os
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad


######################## Chiffrement Vigenère ########################


def vigenere_encrypt(plaintext, key):
    encrypted_text = []
    key_length = len(key)

    for i, char in enumerate(plaintext):
        char_code = (ord(char) + ord(key[i % key_length])) % 256
        encrypted_text.append(chr(char_code))

    encrypted_bytes = ''.join(encrypted_text).encode("utf-8")
    encrypted_base64 = base64.b64encode(encrypted_bytes).decode("utf-8")
    return encrypted_base64

def vigenere_decrypt(ciphertext, key):
    decrypted_text = []
    key_length = len(key)

    decoded_bytes = base64.b64decode(ciphertext)
    decoded_text = decoded_bytes.decode("utf-8")

    for i, char in enumerate(decoded_text):
        char_code = (ord(char) - ord(key[i % key_length]) + 256) % 256
        decrypted_text.append(chr(char_code))

    return ''.join(decrypted_text)

def encrypt_text(texte, cle):
    return vigenere_encrypt(texte, cle)

def decrypt_text(texte_chiffre, cle):
    return vigenere_decrypt(texte_chiffre, cle)


######################## Chiffrement AES-CBC ########################



# Clé secrète (16, 24 ou 32 octets)
SECRET_KEY = b"0123456789abcdef"

def aes_encrypt(plaintext):
    iv = os.urandom(16)  # IV aléatoire
    cipher = AES.new(SECRET_KEY, AES.MODE_CBC, iv)
    padded_text = pad(plaintext.encode(), AES.block_size)
    encrypted_bytes = cipher.encrypt(padded_text)
    
    # Encodage en base64
    iv_base64 = base64.b64encode(iv).decode()
    encrypted_base64 = base64.b64encode(encrypted_bytes).decode()

    # ✅ Utilisation de JSON
    encrypted_data = json.dumps({
        "iv": iv_base64,
        "data": encrypted_base64
    })

    return encrypted_data

def aes_decrypt(ciphertext):
    try:
        print("🔍 Données reçues pour déchiffrement :", ciphertext)

        # ✅ Parser JSON au lieu de splitter
        cipher_dict = json.loads(ciphertext)
        iv = base64.b64decode(cipher_dict["iv"])
        encrypted_bytes = base64.b64decode(cipher_dict["data"])

        # 🔑 Déchiffrement AES-CBC
        cipher = AES.new(SECRET_KEY, AES.MODE_CBC, iv)
        decrypted_bytes = cipher.decrypt(encrypted_bytes)

        # 🛑 Supprimer le padding
        plaintext = unpad(decrypted_bytes, AES.block_size).decode("utf-8")

        print("✅ Message déchiffré :", plaintext)
        return plaintext

    except Exception as e:
        print("❌ Erreur de déchiffrement :", e)
        return None
