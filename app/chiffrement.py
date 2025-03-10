import base64
import json
import os
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from Crypto.Cipher import PKCS1_OAEP
from Crypto.PublicKey import RSA
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.padding import PKCS7


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



SECRET_KEY = b"0123456789abcdef0123456789abcdef"  # Clé 32 bytes pour AES-256

def aes_encrypt(plaintext):
    iv = os.urandom(16)  # IV aléatoire
    cipher = Cipher(algorithms.AES(SECRET_KEY), modes.CBC(iv))
    encryptor = cipher.encryptor()
    padded_text = pad(plaintext.encode(), 16)  # ✅ Ajout du padding
    encrypted_bytes = encryptor.update(padded_text) + encryptor.finalize()
    
    return json.dumps({
        "iv": base64.b64encode(iv).decode(),  # IV en base64
        "data": base64.b64encode(encrypted_bytes).decode()  # Données chiffrées en base64
    })


def aes_decrypt(ciphertext):
    try:
        cipher_dict = json.loads(ciphertext)
        iv = base64.b64decode(cipher_dict["iv"])
        encrypted_bytes = base64.b64decode(cipher_dict["data"])

        cipher = Cipher(algorithms.AES(SECRET_KEY), modes.CBC(iv))
        decryptor = cipher.decryptor()
        decrypted_bytes = decryptor.update(encrypted_bytes) + decryptor.finalize()

        unpadder = PKCS7(128).unpadder()
        plaintext = unpadder.update(decrypted_bytes) + unpadder.finalize()
        
        return plaintext.decode("utf-8")

    except Exception as e:
        print("❌ Erreur de déchiffrement :", e)
        return None


######################## Chiffrement RSA ########################

# Générer une clé RSA de 2048 bits
key = RSA.generate(2048)

# Extraire la clé privée
private_key = key.export_key()
with open("private.pem", "wb") as f:
    f.write(private_key)

# Extraire la clé publique
public_key = key.publickey().export_key()
with open("public.pem", "wb") as f:
    f.write(public_key)

print("✅ Clés RSA générées et enregistrées !")

# Charger la clé privée et publique
def load_rsa_keys():
    with open("private.pem", "rb") as f:
        private_key = RSA.import_key(f.read())
    with open("public.pem", "rb") as f:
        public_key = RSA.import_key(f.read())
    return private_key, public_key

# Fonction pour chiffrer avec la clé publique
def rsa_encrypt(message, public_key):
    cipher = PKCS1_OAEP.new(public_key)
    encrypted_message = cipher.encrypt(message.encode())
    return base64.b64encode(encrypted_message).decode()

# Fonction pour déchiffrer avec la clé privée
def rsa_decrypt(encrypted_message, private_key):
    cipher = PKCS1_OAEP.new(private_key)
    decrypted_message = cipher.decrypt(base64.b64decode(encrypted_message))
    return decrypted_message.decode()

# Charger les clés
private_key, public_key = load_rsa_keys()