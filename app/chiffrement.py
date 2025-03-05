import base64

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