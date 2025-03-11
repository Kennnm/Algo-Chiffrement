from flask import Flask, request, jsonify, render_template
from flask_socketio import SocketIO, send, emit
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP, AES
import base64
import json
from Crypto.Util.Padding import unpad

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

# Générer la clé RSA du serveur
server_key = RSA.generate(2048)
server_public_key = server_key.publickey().export_key()

clients = {}  # Stocke les clés publiques des clients

@app.route("/", methods=["GET"])
def index():
    return render_template("accueil.html")

@app.route("/public_key", methods=["GET"])
def get_public_key():
    return jsonify({"public_key": base64.b64encode(server_public_key).decode()})

@app.route("/get_public_key/<username>", methods=["GET"])
def get_user_public_key(username):
    """ Renvoie la clé publique d'un utilisateur """
    if username in clients:
        public_key_pem = clients[username]["public_key"].export_key().decode()
        return jsonify({"public_key": base64.b64encode(public_key_pem.encode()).decode()})
    else:
        return jsonify({"error": "Utilisateur non trouvé"}), 404


@socketio.on("register")
def handle_register(data):
    """ Gère l'inscription d'un utilisateur en stockant sa clé publique et son SID """
    username = data.get("username")
    client_public_key_pem = data.get("public_key")

    if not username or not client_public_key_pem:
        emit("error", {"message": "Données d'inscription invalides."}, room=request.sid)
        return

    try:
        # Importer la clé publique du client
        client_public_key = RSA.import_key(client_public_key_pem)

        # Stocker le SID en plus de la clé publique
        clients[username] = {
            "public_key": client_public_key,
            "sid": request.sid  # Stocke l'ID de session WebSocket
        }
        
        print(f"{username} s'est connecté")

        emit("registered", {"message": "Clé publique enregistrée."}, room=request.sid)
        socketio.emit("user_update")  # Met à jour la liste des utilisateurs

    except Exception as e:
        print(f"Erreur lors de l'importation de la clé publique : {e}")
        emit("error", {"message": "Erreur lors de l'importation de la clé publique."}, room=request.sid)


@socketio.on("get_users")
def send_users():
    """ Envoie la liste des utilisateurs connectés à tous les clients """
    user_list = list(clients.keys())
    socketio.emit("liste_utilisateurs", user_list)

@socketio.on("send_message")
def handle_message(data):
    """ Gère l'envoi et la réception des messages chiffrés """
    sender = data.get("sender")
    recipient = data.get("recipient")

    # Vérifier si le destinataire est valide
    if recipient not in clients:
        print(f"Destinataire inconnu : {recipient}")
        return

    recipient_sid = clients[recipient]["sid"]
    sender_sid = clients[sender]["sid"]
    recipient_public_key = clients[recipient]["public_key"]
    public_key_pem = recipient_public_key.export_key().decode()  # Convertir en PEM lisible

    # Transmettre les données chiffrées directement sans déchiffrement
    message_data = {
        "sender": sender,
        "encrypted_aes_key": data.get("encrypted_aes_key"),
        "encrypted_aes_key_for_sender": data.get("encrypted_aes_key_for_sender"),
        "iv": data.get("iv"),
        "message": data.get("message"),
    }
    # Envoie au destinataire
    emit("receive_message", message_data, room=recipient_sid)
    # Envoie aussi à l'expéditeur pour l'afficher dans son interface
    emit("receive_message", message_data, room=sender_sid)


if __name__ == "__main__":
    socketio.run(app, host="127.0.0.1", port=5000, debug=True)
