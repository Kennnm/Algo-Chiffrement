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
    username = data["username"]
    clients[username] = request.sid
    print(f"{username} s'est connecté")
    emit("liste_utilisateurs", list(clients.keys()), broadcast=True)

@socketio.on("message_prive")
def handle_message_prive(data):
    """Chiffrement et envoi d'un message privé"""
    sender = data["expediteur"]
    recipient = data["destinataire"]
    message_clair = data["message"]
    print("message_clair",message_clair)
    # Chiffrer UNIQUEMENT le texte du message
    message_chiffre = chiffrement.encrypt_text(message_clair, "clé")  # Clé Vigenère
    message_dechiffre = chiffrement.decrypt_text(message_chiffre, "clé")

    # print(f"Message chiffré envoyé à {recipient}: {message_chiffre}")
    # print("message_dechiffre",message_dechiffre)

    if recipient in clients:
        print("Message envoyé:", message_chiffre)
        emit("message_recu", {"expediteur": sender, "message": message_chiffre}, room=clients[recipient])
    else:
        emit("erreur", {"message": "Utilisateur non trouvé"}, room=clients[sender])


@socketio.on("disconnect")
def handle_disconnect():
    user = [name for name, sid in clients.items() if sid == request.sid]
    if user:
        del clients[user[0]]
        print(f"{user[0]} s'est déconnecté")
        emit("liste_utilisateurs", list(clients.keys()), broadcast=True)

if __name__ == "__main__":
    socketio.run(app, host="127.0.0.1", port=5000, debug=True)
