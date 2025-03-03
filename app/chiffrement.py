import json
import base64



def vigenere_encrypt(plaintext, key):
    """Chiffre une chaîne de caractères avec Vigenère"""
    encrypted_text = []
    key_length = len(key)
    key_as_int = [ord(i) for i in key]
    plaintext_int = [ord(i) for i in plaintext]
    
    for i in range(len(plaintext_int)):
        value = (plaintext_int[i] + key_as_int[i % key_length]) % 128  # Utilisation de 128 pour ASCII complet
        encrypted_text.append(chr(value))
    
    return ''.join(encrypted_text)


def vigenere_decrypt(ciphertext, key):
    """Déchiffre une chaîne de caractères chiffrée avec Vigenère"""
    decrypted_text = []
    key_length = len(key)
    key_as_int = [ord(i) for i in key]
    ciphertext_int = [ord(i) for i in ciphertext]
    
    for i in range(len(ciphertext_int)):
        value = (ciphertext_int[i] - key_as_int[i % key_length]) % 128  # Déchiffrement avec modulo 128
        decrypted_text.append(chr(value))
    
    return ''.join(decrypted_text)


def encrypt_text(text, key):
    """Chiffre une chaîne de texte et l'encode en Base64"""
    encrypted_text = vigenere_encrypt(text, key)  # Chiffrer
    return base64.b64encode(encrypted_text.encode()).decode()  # Convertir en Base64


def decrypt_text(encrypted_data, key):
    """Déchiffre une chaîne de texte encodée en Base64"""
    try:
        encrypted_data = base64.b64decode(encrypted_data).decode()  # Décoder Base64
        return vigenere_decrypt(encrypted_data, key)  # Déchiffrer
    except (UnicodeDecodeError, binascii.Error):
        print("Erreur de décodage")
        return ""

