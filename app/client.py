import asyncio
import websockets
import sys
import json
from chiffrement import *

async def receive_messages(websocket):
    """Boucle qui écoute en permanence les messages du serveur."""
    while True:
        message = await websocket.recv()
        try:
            data = json.loads(message)
            decrypted_data = decrypt_dict(data, "clé")  # Déchiffrer le message
            if decrypted_data["type"] == "liste_destinataires":
                print("\nListe des destinataires possibles: \n", decrypted_data["liste_destinataires"])
            elif decrypted_data["type"] == "message_prive":
                print(f"\r{decrypted_data['expediteur']}: {decrypted_data['message']}\n")
            elif decrypted_data["type"] == "erreur":
                print(f"\rErreur: {decrypted_data['message']}\n")
            else:
                print(f"\n[Message inconnu]: {data}\n")
        except json.JSONDecodeError:
            print(f"\r{message}\n")
        sys.stdout.write("Vous: ")
        sys.stdout.flush()

async def send_messages(websocket, destinataire):
    """Boucle pour envoyer les messages avec un délai, sans bloquer."""
    while True:
        message = await asyncio.to_thread(input, "Vous: ")
        if message.lower() == "exit":
            print("Déconnexion...")
            await websocket.close()
            break
        message_prive = {"type": "message_prive", "destinataire": destinataire, "message": message}
        encrypted_message_prive = encrypt_dict(message_prive, "clé")  # Chiffrer le message
        await websocket.send(encrypted_message_prive)
        await asyncio.sleep(0.5)  # petite pause pour éviter un envoi trop rapide

async def start_client():
    uri = "ws://localhost:8765"
    async with websockets.connect(uri) as websocket:
        print("Connecté au serveur WebSocket")
        
        # Envoi du login sous forme JSON
        username = input("Entrez votre nom d'utilisateur: ")
        login = {"type": "login", "username": username}
        encrypted_login = encrypt_dict(login, "clé")  # Chiffrer le login
        await websocket.send(encrypted_login)
        
        # Choix du menu
        menu = input("Que souhaitez-vous faire ? \n1. Envoyer un message à quelqu'un \n2. Quitter\n")
        if menu == "1":
            demande_liste_destinataires = {"type": "liste_destinataires"}
            demande_liste_destinataires_encrypted = encrypt_dict(demande_liste_destinataires, "clé")  # Chiffrer la demande
            await websocket.send(demande_liste_destinataires_encrypted)
            
            liste_destinataires = await websocket.recv()
            try:
                decrypted_data = decrypt_dict(liste_destinataires, "clé")  # Déchiffrer le message
                if decrypted_data["type"] == "liste_destinataires":
                    destinataire = decrypted_data["liste_destinataires"]
                    print("Liste des destinataires possibles: \n")
                    for item in decrypted_data["liste_destinataires"]:
                        print(f" - {item['username']} \n")
                else:
                    print("Réponse inattendue: ", decrypted_data)
            except json.JSONDecodeError:
                print("Erreur de décodage JSON: ", decrypted_data)
                
            destinataire = input("Entrez le nom de la personne à qui vous voulez envoyer un message: \n")
            # Envoyer le signal 'ready' pour indiquer que l'utilisateur est prêt
            ready = {"type": "ready"}
            ready_encrypted = encrypt_dict(ready, "clé")  # Chiffrer le message
            await websocket.send(ready_encrypted)
            
            # Lancer immédiatement l'écoute des messages
            receive_task = asyncio.create_task(receive_messages(websocket))
            
            # Lancer l'envoi des messages sans attendre
            send_task = asyncio.create_task(send_messages(websocket, destinataire))

            # Attendre que l'une des tâches se termine
            await asyncio.gather(receive_task, send_task)

            # Si l'utilisateur quitte, on ferme la connexion
            receive_task.cancel()

asyncio.run(start_client())
