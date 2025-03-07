from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit
import chiffrement  # Module de chiffrement
import json

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")  # Autoriser tous les clients

clients = {}  # Stockage des utilisateurs connectés

@app.route("/")
def index():
    return render_template("accueil.html")

@socketio.on("connect")
def handle_connect():
    print("Un utilisateur s'est connecté")

@socketio.on("login")
def handle_login(data):
    try:
        # 🔓 Déchiffrer les données du login
        decrypted_json = chiffrement.vigenere_decrypt(data["encrypted_data"], "cle")
        login_data = json.loads(decrypted_json)

        if isinstance(login_data, list) and len(login_data) == 2 and login_data[0] == "login":
            user_info = login_data[1]
            username = user_info.get("username")

            if username:
                clients[username] = request.sid
                print(f"{username} s'est connecté")

                # 🔹 Chiffrer la liste des utilisateurs avant envoi
                encrypted_users = chiffrement.vigenere_encrypt(json.dumps(list(clients.keys())), "cle")
                emit("liste_utilisateurs", {"encrypted_data": encrypted_users}, broadcast=True)
            else:
                print("❌ Erreur : 'username' est manquant !")
        else:
            print("❌ Format JSON incorrect :", login_data)

    except Exception as e:
        print("❌ Erreur lors du traitement du login :", e)



@socketio.on("message_chiffre")
def handle_message_prive(data):
    """Transmet un message privé sans le modifier"""
    try:
        
        # 🔹 Déchiffrement du message reçu
        decrypted_data = chiffrement.vigenere_decrypt(data["data"], "cle")
        message_obj = json.loads(decrypted_data)  # Transformer en JSON
        
        if message_obj["type"] == "message_prive":      
            sender = message_obj["expediteur"]
            recipient = message_obj["destinataire"]
            message_chiffre = message_obj["message"]

            print(f"📩 Message reçu de {sender} pour {recipient}: {message_chiffre}")
            
            encrypted_message = chiffrement.vigenere_encrypt(message_chiffre, "cle")  # Chiffrer le message avant envoi
            encrypted_sender = chiffrement.vigenere_encrypt(sender, "cle")  # Chiffrer l'expéditeur avant envoi

            if recipient in clients:
                emit("message_recu", {"data": encrypted_message, "sender": encrypted_sender}, room=clients[recipient])
            else:
                emit("erreur", {"message": "Utilisateur non trouvé"}, room=clients[sender])
        else:
                print("Type de message inconnu :", message_obj["type"])
                emit("erreur", {"message": "Type de message invalide"}, room=clients[sender])
                
    except Exception as e:
        print("Erreur de déchiffrement :", str(e))
        emit("erreur", {"message": "Déchiffrement impossible"}, room=clients[sender])
    


@socketio.on("disconnect")
def handle_disconnect():
    user = [name for name, sid in clients.items() if sid == request.sid]
    if user:
        del clients[user[0]]
        print(f"{user[0]} s'est déconnecté")
        encrypted_users = chiffrement.vigenere_encrypt(json.dumps(list(clients.keys())), "cle")
        emit("liste_utilisateurs", {"encrypted_data": encrypted_users}, broadcast=True)


if __name__ == "__main__":
    socketio.run(app, host="127.0.0.1", port=5000, debug=True)
