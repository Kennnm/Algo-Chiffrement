from flask import Flask, render_template, request
from flask_socketio import SocketIO, send, emit, join_room, leave_room
import chiffrement  # Import de ton module de chiffrement

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")  # Autoriser tous les clients

clients = {}  # Dictionnaire des utilisateurs connectés

@app.route("/")
def index():
    return render_template("accueil.html")

@socketio.on("connect")
def handle_connect():
    print("Un utilisateur s'est connecté")

@socketio.on("login")
def handle_login(data):
    """Connexion d'un utilisateur"""    
    username = data["username"]
    clients[username] = request.sid  # Associer username à son ID Socket
    print(f"{username} s'est connecté")

    # Envoyer la liste des utilisateurs connectés
    emit("liste_utilisateurs", list(clients.keys()), broadcast=True)

@socketio.on("message_prive")
def handle_message_prive(data):
    """Envoi de message privé"""
    sender = data["expediteur"]
    recipient = data["destinataire"]
    message = chiffrement.encrypt_dict({"message": data["message"]}, "clé")  # Chiffrer le message

    if recipient in clients:
        emit("message_recu", {"expediteur": sender, "message": message}, room=clients[recipient])
    else:
        emit("erreur", {"message": "Utilisateur non trouvé"}, room=clients[sender])

@socketio.on("disconnect")
def handle_disconnect():
    """Déconnexion d'un utilisateur"""
    user = [name for name, sid in clients.items() if sid == request.sid]
    if user:
        del clients[user[0]]
        print(f"{user[0]} s'est déconnecté")
        emit("liste_utilisateurs", list(clients.keys()), broadcast=True)

if __name__ == "__main__":
    socketio.run(app, host="127.0.0.1", port=5000, debug=True)
