import asyncio
import websockets
import json
from chiffrement import *

clients = {}  # Utilisation d'un dictionnaire pour stocker les clients


async def handle_client(websocket):
    # Recevoir le nom d'utilisateur et l'ajouter au dictionnaire avec le WebSocket comme valeur
    username_data = await websocket.recv()
    decrypted_username = decrypt_dict(username_data, "clé")  # Déchiffrer le nom d'utilisateur
    username = decrypted_username["username"]
    clients[username] = websocket  # Ajouter le client avec son nom d'utilisateur comme clé
    print(f"({username}) s'est connecté")

    # Demander au client de choisir une option
    choix_menu_encrypted = await websocket.recv()
    choix_user_menu = decrypt_dict(choix_menu_encrypted, "clé")  # Déchiffrer le choix du menu
    if choix_user_menu["type"] == "liste_destinataires":
        liste_destinataires = [{"username": client} for client in clients if client != username]  # Liste des autres clients
        data_clair = {"type": "liste_destinataires", "liste_destinataires": liste_destinataires}
        data_chiffre = encrypt_dict(data_clair, "clé")  # Chiffrer la liste des destinataires
        await websocket.send(data_chiffre)

    try:
        async for message in websocket:
            data_encrypted = message
            data_decrypted = decrypt_dict(data_encrypted, "clé")  # Déchiffrer le message
            if data_decrypted["type"] == "ready":
                print(f"{username} est prêt")
                continue
                        
            if data_decrypted["type"] == "message_prive":

                print(f"Message reçu de {username}: {data_decrypted['message']}")

                destinataire = data_decrypted["destinataire"]
                if destinataire in clients:
                    data_clair = {"type": "message_prive", "expediteur": username, "message": data_decrypted["message"]}
                    data_chiffre = encrypt_dict(data_clair, "clé")  # Chiffrer le message
                    await clients[destinataire].send(json.dumps(data_chiffre))
                else:
                    erreur = {"type": "erreur", "message": f"Destinataire {data_decrypted['destinataire']} non trouvé."}
                    data_chiffre = encrypt_dict(erreur, "clé")  # Chiffrer le message d'erreur
                    await websocket.send(json.dumps(data_chiffre))
            else:
                erreur = {"type": "erreur", "message": "Commande inconnue."}
                data_chiffre = encrypt_dict(erreur, "clé")
                await websocket.send(json.dumps(data_chiffre))
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
