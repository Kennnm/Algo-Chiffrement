import asyncio
import websockets
import sys
import json

async def receive_messages(websocket):
    """Boucle qui écoute en permanence les messages du serveur."""
    while True:
        message = await websocket.recv()
        try:
            data = json.loads(message)
            if data["type"] == "liste_destinataires":
                print("\nListe des destinataires possibles: \n", data["liste_destinataires"])
            elif data["type"] == "message_prive":
                print(f"\r{data['expediteur']}: {data['message']}\n")
            elif data["type"] == "erreur":
                print(f"\rErreur: {data['message']}\n")
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
        await websocket.send(json.dumps(message_prive))
        await asyncio.sleep(0.5)  # petite pause pour éviter un envoi trop rapide

async def start_client():
    uri = "ws://localhost:8765"
    async with websockets.connect(uri) as websocket:
        print("Connecté au serveur WebSocket")
        
        # Envoi du login sous forme JSON
        username = input("Entrez votre nom d'utilisateur: ")
        login = {"type": "login", "username": username}
        await websocket.send(json.dumps(login))
        
        # Choix du menu
        menu = input("Que souhaitez-vous faire ? \n1. Envoyer un message à quelqu'un \n2. Quitter\n")
        if menu == "1":
            demande_liste_destinataires = {"type": "liste_destinataires"}
            await websocket.send(json.dumps(demande_liste_destinataires))
            
            liste_destinataires = await websocket.recv()
            try:
                data = json.loads(liste_destinataires)
                if data["type"] == "liste_destinataires":
                    print("Liste des destinataires possibles: \n")
                    for item in data["liste_destinataires"]:
                        print(f" - {item['username']} \n")
                else:
                    print("Réponse inattendue: ", data)
            except json.JSONDecodeError:
                print("Erreur de décodage JSON: ", liste_destinataires)
                
            destinataire = input("Entrez le nom de la personne à qui vous voulez envoyer un message: \n")
            # Envoyer le signal 'ready' pour indiquer que l'utilisateur est prêt
            ready = {"type": "ready"}
            await websocket.send(json.dumps(ready))
            
            # Lancer immédiatement l'écoute des messages
            receive_task = asyncio.create_task(receive_messages(websocket))
            
            # Lancer l'envoi des messages sans attendre
            send_task = asyncio.create_task(send_messages(websocket, destinataire))

            # Attendre que l'une des tâches se termine
            await asyncio.gather(receive_task, send_task)

            # Si l'utilisateur quitte, on ferme la connexion
            receive_task.cancel()

asyncio.run(start_client())
