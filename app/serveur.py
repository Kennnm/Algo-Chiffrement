import asyncio
import websockets
import json

clients = {}  # Utilisation d'un dictionnaire pour stocker les clients

def vigenere_encrypt(plaintext, key):
    encrypted_text = []
    key_length = len(key)
    key_as_int = [ord(i) for i in key]
    plaintext_int = [ord(i) for i in plaintext]
    for i in range(len(plaintext_int)):
        value = (plaintext_int[i] + key_as_int[i % key_length]) % 26
        encrypted_text.append(chr(value + 65))
    return ''.join(encrypted_text)

async def handle_client(websocket):
    # Recevoir le nom d'utilisateur et l'ajouter au dictionnaire avec le WebSocket comme valeur
    username = await websocket.recv()
    login_data = json.loads(username)
    username = login_data["username"]
    clients[username] = websocket  # Ajouter le client avec son nom d'utilisateur comme clé
    print(f"({username}) s'est connecté")

    # Demander au client de choisir une option
    message = await websocket.recv()
    choix_user_menu = json.loads(message)
    if choix_user_menu["type"] == "liste_destinataires":
        liste_destinataires = [{"username": client} for client in clients if client != username]  # Liste des autres clients
        data = {"type": "liste_destinataires", "liste_destinataires": liste_destinataires}
        await websocket.send(json.dumps(data))

    try:
        async for message in websocket:
            
            data = json.loads(message)
            if data["type"] == "ready":
                print(f"{username} est prêt")
                continue
            
            print(data)
            
            if data["type"] == "message_prive":

                encrypted_data = vigenere_encrypt(data, "clé")  # Chiffrer le message
                print(f"Message reçu de {username}: {message}")

                destinataire = data["destinataire"]
                if destinataire in clients:
                    data = {"type": "message_prive", "expediteur": username, "message": data["message"]}
                    await clients[destinataire].send(json.dumps(encrypted_data))
                else:
                    error = {"type": "erreur", "message": f"Destinataire {data['destinataire']} non trouvé."}
                    await websocket.send(json.dumps(error))
            else:
                error = {"type": "erreur", "message": "Commande inconnue."}
                await websocket.send(json.dumps(error))
    except websockets.exceptions.ConnectionClosed:
        print(f"{username} s'est déconnecté")
    finally:
        # Retirer le client du dictionnaire lorsque la connexion est fermée
        clients.pop(username, None)

async def start_server():
    server = await websockets.serve(handle_client, "localhost", 8765)
    print("Serveur WebSocket démarré sur ws://localhost:8765")
    await server.wait_closed()

# Lancer le serveur
asyncio.run(start_server())
