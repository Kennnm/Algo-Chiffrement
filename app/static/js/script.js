const socket = io();

// Connexion au serveur
socket.on("connect", () => {
    console.log("Connecté au serveur Socket.IO");
});

// Gestion de la connexion utilisateur
function login() {
    let username = document.getElementById("username").value;
    if (username.trim() !== "") {
        socket.emit("login", { username });
        document.getElementById("chatbox").style.display = "block";
    }
}

// Affichage de la liste des utilisateurs connectés
socket.on("liste_utilisateurs", (users) => {
    let usersList = document.getElementById("usersList");
    usersList.innerHTML = "";
    users.forEach((user) => {
        let option = document.createElement("option");
        option.value = user;
        option.innerText = user;
        usersList.appendChild(option);
    });
});

// Envoi d'un message privé
function sendMessage() {
    let message = document.getElementById("message").value;
    let recipient = document.getElementById("usersList").value;
    socket.emit("message_prive", { expediteur: "Moi", destinataire: recipient, message });
}

// Fonction de déchiffrement Vigenère
function vigenereDecrypt(ciphertext, key) {
    let decryptedText = [];
    let keyLength = key.length;
    let keyAsInt = [...key].map(char => char.charCodeAt(0));
    let ciphertextInt = [...ciphertext].map(char => char.charCodeAt(0));

    for (let i = 0; i < ciphertextInt.length; i++) {
        let value = (ciphertextInt[i] - keyAsInt[i % keyLength] + 128) % 128; // Déchiffrement avec Vigenère
        decryptedText.push(String.fromCharCode(value));
    }
    return decryptedText.join('');
}

// Fonction pour décoder base64 et déchiffrer
function base64DecodeAndDecrypt(base64Data, key) {
    let decodedData = atob(base64Data);  // Décoder base64
    return vigenereDecrypt(decodedData, key);  // Déchiffrer avec Vigenère
}

// Réception de messages
socket.on("message_recu", (data) => {
    let decryptedMessage = base64DecodeAndDecrypt(data.message, "clé");
    console.log("Message reçu (Base64):", data.message);
    console.log("Message déchiffré:", decryptedMessage);

    let msgList = document.getElementById("messages");
    let li = document.createElement("li");
    li.innerText = `${data.expediteur}: ${decryptedMessage}`;
    msgList.appendChild(li);
});
