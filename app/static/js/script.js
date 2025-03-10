const socket = io.connect('http://127.0.0.1:5000');

socket.on('connect', () => {
    console.log('Connecté au serveur');
});

let public_key = "";  // Variable globale pour stocker la clé publique

socket.emit("get_public_key"); // Demande la clé publique lors de la connexion

socket.on("public_key", function(key) {
    public_key = key; // Stocker la clé publique reçue
    console.log("🔑 Clé publique reçue :", public_key);
});


socket.on("liste_utilisateurs", (data) => {
    try {
        let decryptedUsersJson = aesDecrypt(data.encrypted_data);
        let usersList = JSON.parse(decryptedUsersJson);

        const username = document.getElementById('username').value; // Récupérer le nom d'utilisateur actuel
        const userList = document.getElementById('user-list');
        userList.innerHTML = '';
        console.log("🔐 Liste des utilisateurs chiffrée :", data.encrypted_data);
        usersList.forEach(user => {
            if (user !== username) { // Filtrer l'utilisateur connecté
                const li = document.createElement('li');
                li.textContent = user;

                // Ajouter un événement de clic pour sélectionner un destinataire
                li.addEventListener('click', function() {
                    console.log("utilisateur sélectionné :", user);
                    document.getElementById('recipient').value = user; // Mettre à jour le champ destinataire
                    document.querySelectorAll('.sidebar ul li').forEach(li => li.classList.remove('selected'));
                    this.classList.add('selected'); // Ajouter la classe sélectionnée
                    
                    // Rendre visible la section de messages et le formulaire de message
                    document.querySelector('.login-form').style.display = 'none';

                    document.querySelector('.message-form').style.display = 'block';  // Afficher la zone de saisie du message
                    document.querySelector('.messages').style.display = 'block'; // Afficher la section des messages
                });
                

                userList.appendChild(li);
            }
        });

    } catch (error) {
        console.error("❌ Erreur lors du déchiffrement de la liste des utilisateurs :", error);
    }
});

socket.on("message_recu", (data) => {
    console.log("🔐 Message chiffré reçu :", data.data);

    const encryptedMessage = data.data;
    const encryptedSender = data.sender;

    // 🔹 Déchiffrer TOUTE la structure JSON
    const decryptedData = aesDecrypt(encryptedMessage);
    console.log("✅ JSON déchiffré :", decryptedData);
    const decryptedSender = aesDecrypt(encryptedSender);

    if (decryptedData) {
        const message = decryptedData;
        const sender = decryptedSender;
        console.log("📩 Message final :", message);

        const currentUser = document.getElementById('username').value;
        const isSentByMe = false;

        // ✅ Vérifier si le message est déjà affiché
        if (!document.querySelector(`[data-id="${message}-${currentUser}"]`)) {
            afficherMessage(sender, message, "received");
        } else {
            console.warn("⚠️ Message déjà affiché, annulation :", message);
        }
    }
    else {
        console.error("❌ Erreur de déchiffrement ou format inattendu");
    }
});


socket.on('erreur', (data) => {
    alert(data.message);
});


function login() {
    console.log("🚀 Fonction login() appelée !");
    
    const username = document.getElementById('username').value;
    if (username.trim() !== '') {
        let loginData = {
            type: "login",
            data: { "username": username }
        };

        let jsonString = JSON.stringify(loginData);
        console.log("📄 JSON généré :", jsonString);

        let encryptedData = aesEncrypt(jsonString); // ✅ Utiliser la fonction aesEncrypt()

        console.log("🔐 Donnée chiffrée envoyée :", encryptedData);
        socket.emit('login', { encrypted_data: encryptedData });
    } else {
        console.error("❌ Erreur: Nom d'utilisateur vide");
    }
}

// Fonction pour envoyer un message
function sendMessage() {
    const recipient = document.getElementById('recipient').value;
    const message = document.getElementById('message').value;
    const sender = document.getElementById('username').value;

    if (recipient.trim() !== '' && message.trim() !== '') {
        // 🔹 Construire le JSON à chiffrer
        const dataToEncrypt = JSON.stringify({
            type: "message_prive",
            expediteur: sender,
            destinataire: recipient,
            message: message
        });

        // 🔹 Chiffrer le JSON avant l'envoi
        const encryptedMessage = aesEncrypt(dataToEncrypt);

        // 🔹 Envoyer le message chiffré
        socket.emit('message_chiffre', { data: encryptedMessage });

        // 📌 Afficher immédiatement le message envoyé dans l'interface
        afficherMessage(sender, message, "sent");

        // 🔹 Vider la zone de texte après l'envoi
        document.getElementById('message').value = "";
    }
} 

// Fonction de chiffrement RSA
function rsaEncrypt(message) {
    // Utiliser une bibliothèque comme JSEncrypt pour chiffrer avec la clé publique RSA
    const encrypt = new JSEncrypt();
    
    // La clé publique RSA devrait être récupérée depuis le serveur et définie ici
    encrypt.setPublicKey(publicKey);  // publicKey doit être définie dans le script côté client
    
    // Retourne le message chiffré en base64
    return encrypt.encrypt(message);
}

// Exemple de clé publique RSA (à récupérer depuis le serveur au début de la session)
let publicKey = "";  // Cette clé publique sera mise à jour après réception du serveur

// Exemple de fonction pour récupérer la clé publique du serveur lors de la connexion initiale
socket.on('public_key', function(key) {
    publicKey = key;
});
      


function shouldScrollToBottom() {
    const messagesContainer = document.getElementById("messages");
    return messagesContainer.scrollTop + messagesContainer.clientHeight >= messagesContainer.scrollHeight - 10;
}

function afficherMessage(expediteur, message, type) {
    const messagesContainer = document.getElementById("messages");
    const shouldScroll = shouldScrollToBottom(); // Vérifie si on est déjà en bas avant d'ajouter un message

    const li = document.createElement("li");
    li.textContent = `${expediteur}: ${message}`;

    if (type === "sent") {
        li.classList.add("message-sent");
    } else {
        li.classList.add("message-received");
    }

    messagesContainer.appendChild(li);

    // 🔥 Si l'utilisateur était déjà en bas, on scroll automatique
    if (shouldScroll) {
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }
}



const SECRET_KEY = "0123456789abcdef0123456789abcdef"; // 32 caractères (256 bits)

function aesEncrypt(plaintext) {
    let key = CryptoJS.enc.Utf8.parse(SECRET_KEY);
    let iv = CryptoJS.lib.WordArray.random(16); // IV aléatoire

    let encrypted = CryptoJS.AES.encrypt(plaintext, key, {
        iv: iv, 
        mode: CryptoJS.mode.CBC,
        padding: CryptoJS.pad.Pkcs7
    });

    let ivBase64 = CryptoJS.enc.Base64.stringify(iv);
    let encryptedBase64 = CryptoJS.enc.Base64.stringify(encrypted.ciphertext);

    // ✅ Utiliser JSON pour stocker IV et data
    let finalCiphertext = JSON.stringify({
        iv: ivBase64,
        data: encryptedBase64
    });

    console.log("🔐 Message chiffré envoyé :", finalCiphertext);  
    return finalCiphertext;
}     


function aesDecrypt(ciphertext) {
    try {
        let parsedData = JSON.parse(ciphertext);  // ✅ Parse JSON d'abord
        let iv = CryptoJS.enc.Base64.parse(parsedData.iv);
        let encryptedBytes = CryptoJS.enc.Base64.parse(parsedData.data);
        let key = CryptoJS.enc.Utf8.parse(SECRET_KEY);

        let decrypted = CryptoJS.AES.decrypt(
            { ciphertext: encryptedBytes },  // ✅ Correct
            key,
            { iv: iv, mode: CryptoJS.mode.CBC, padding: CryptoJS.pad.Pkcs7 }
        );

        let decryptedText = decrypted.toString(CryptoJS.enc.Utf8);  // ✅ Convertir en texte

        if (!decryptedText) {
            throw new Error("Le texte déchiffré est vide ou invalide.");
        }

        return decryptedText;
    } catch (error) {
        console.error("❌ Erreur de déchiffrement :", error);
        return null;
    }
}

