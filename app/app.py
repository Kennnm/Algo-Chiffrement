from flask import Flask, request, jsonify, render_template
from flask_socketio import SocketIO, emit
from Crypto.PublicKey import RSA
from flask_sqlalchemy import SQLAlchemy
import base64
import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///chat.db'  # Base de données SQLite
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
socketio = SocketIO(app, cors_allowed_origins="*")

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    public_key = db.Column(db.Text, nullable=False)

class Conversation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user1 = db.Column(db.String(50), nullable=False)
    user2 = db.Column(db.String(50), nullable=False)

    def __init__(self, user1, user2):
        self.user1 = user1
        self.user2 = user2


# Modèle de base de données pour stocker les messages
class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender = db.Column(db.String(50), nullable=False)
    recipient = db.Column(db.String(50), nullable=False)
    conversation_id = db.Column(db.String(100), nullable=False)  
    encrypted_aes_key = db.Column(db.Text, nullable=False)
    encrypted_aes_key_for_sender = db.Column(db.Text, nullable=False)
    iv = db.Column(db.Text, nullable=False)
    message = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    is_read = db.Column(db.Boolean, default=False)  # Par défaut, le message est non lu

connected_users = {}  # Associe chaquue utilisateur à son SID

def save_user(username, public_key):
    user = User.query.filter_by(username=username).first()
    if not user:
        user = User(username=username, public_key=public_key)
        db.session.add(user)
    else:
        user.public_key = public_key
    db.session.commit()

@app.route("/", methods=["GET"])
def index():
    return render_template("accueil.html")

@socketio.on("store_public_key")
def store_public_key(data):
    username = data.get("username")
    public_key = data.get("public_key")

    if username and public_key:
        save_user(username, public_key)  # Enregistrement dans la base de données
        connected_users[username] = request.sid  # Associe l'utilisateur à son SID
        print(f"Clé publique de {username} enregistrée.")


@app.route("/get_public_key/<username>", methods=["GET"])
def get_user_public_key(username):
    """ Renvoie la clé publique d'un utilisateur """
    user = User.query.filter_by(username=username).first()
    if user:
        return jsonify({"public_key": base64.b64encode(user.public_key.encode()).decode()})
    else:
        return jsonify({"error": "Utilisateur non trouvé"}), 404


@socketio.on("get_users")
def send_users():
    """ Envoie la liste des utilisateurs enregistrés depuis la base de données """
    try:
        users = User.query.with_entities(User.username).all()  # Récupère uniquement les noms d'utilisateur
        user_list = [user.username for user in users]  # Convertit en liste simple
        
        socketio.emit("liste_utilisateurs", user_list)  # Envoie la liste à tous les clients connectés
    except Exception as e:
        print(f"Erreur lors de la récupération des utilisateurs : {e}")
        emit("error", {"message": "Erreur lors de la récupération des utilisateurs."}, room=request.sid)



@socketio.on("send_message")
def handle_message(data):
    """ Gère l'envoi et la réception des messages chiffrés """
    sender = data.get("sender")
    recipient = data.get("recipient")

    # Vérifier si le destinataire est valide
    if recipient not in connected_users:
        print(f"Destinataire inconnu : {recipient}")
        return

    recipient_sid = connected_users[recipient]
    sender_sid = connected_users[sender]

    # Vérifier si une conversation existe déjà entre sender et recipient
    conversation = Conversation.query.filter(
        ((Conversation.user1 == sender) & (Conversation.user2 == recipient)) |
        ((Conversation.user1 == recipient) & (Conversation.user2 == sender))
    ).first()

    # Si la conversation n'existe pas, la créer
    if not conversation:
        conversation = Conversation(user1=sender, user2=recipient)
        db.session.add(conversation)
        db.session.commit()  # On commit pour générer un ID de conversation

    # Vérifier que conversation.id est bien défini
    if not conversation.id:
        print("Erreur : conversation_id est None après la création de la conversation.")
        return

    new_message = Message(
        sender=sender,
        recipient=recipient,
        conversation_id=conversation.id,
        encrypted_aes_key=data.get("encrypted_aes_key"),
        encrypted_aes_key_for_sender=data.get("encrypted_aes_key_for_sender"),
        iv=data.get("iv"),
        message=data.get("message"),
        is_read=False
    )
    
        # Ajouter et enregistrer le message en base de données
    db.session.add(new_message)
    db.session.commit()
    
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
    
     # Met à jour le compteur de messages non lus pour le destinataire
    unread_count = Message.query.filter_by(recipient=recipient, is_read=False).count()
    socketio.emit("update_unread_count", {"username": recipient, "unread_count": unread_count}, room=recipient_sid)


@app.route("/get_messages/<sender>/<recipient>", methods=["GET"])
def get_messages(sender, recipient):
    """ Récupère l'historique des messages entre deux utilisateurs """
    messages = Message.query.filter(
        ((Message.sender == sender) & (Message.recipient == recipient)) |
        ((Message.sender == recipient) & (Message.recipient == sender))
    ).order_by(Message.timestamp.asc()).all()
    return jsonify([
        {
            "sender": msg.sender,
            "encrypted_aes_key": msg.encrypted_aes_key,
            "encrypted_aes_key_for_sender": msg.encrypted_aes_key_for_sender,
            "iv": msg.iv,
            "message": msg.message,
            "timestamp": msg.timestamp.isoformat()
        }
        for msg in messages
    ])


@app.route("/unread_messages/<username>", methods=["GET"])
def get_unread_messages(username):
    unread_counts = (
        db.session.query(Message.sender, db.func.count(Message.id))
        .filter_by(recipient=username, is_read=False)
        .group_by(Message.sender)
        .all()
    )

    # Transformer le résultat en dictionnaire { "expediteur1": nombre, "expediteur2": nombre }
    unread_dict = {sender: count for sender, count in unread_counts}

    print(f"Messages non lus pour {username} :", unread_dict)  # Ajout d'un log pour vérifier
    return jsonify(unread_dict)


@app.route("/mark_as_read/<sender>/<recipient>", methods=["POST"])
def mark_as_read(sender, recipient):
    """ Marque tous les messages non lus d'une conversation comme lus """
    try:
        updated_rows = Message.query.filter_by(sender=sender, recipient=recipient, is_read=False).update({"is_read": True})
        db.session.commit()

        # Met à jour le compteur de messages non lus
        unread_count = Message.query.filter_by(recipient=recipient, is_read=False).count()

        # Vérifier si le destinataire est connecté
        recipient_sid = connected_users.get(recipient)
        if recipient_sid:
            socketio.emit("update_unread_count", {"username": recipient, "unread_count": unread_count}, room=recipient_sid)

        return jsonify({"message": f"{updated_rows} messages marqués comme lus"})

    except Exception as e:
        print(f"Erreur lors du marquage des messages comme lus: {e}")
        return jsonify({"error": "Erreur serveur"}), 500


@socketio.on("disconnect")
def handle_disconnect():
    """ Supprime l'utilisateur de la liste des connectés quand il se déconnecte """
    for username, sid in list(connected_users.items()):
        if sid == request.sid:
            print(f"{username} s'est déconnecté.")
            del connected_users[username]
            break
    
    # Mettre à jour la liste des utilisateurs en temps réel
    send_users()


if __name__ == "__main__":
    with app.app_context():
        db.drop_all()  # Supprime toutes les tables
        db.create_all()
    socketio.run(app, host="127.0.0.1", port=5000, debug=True)
