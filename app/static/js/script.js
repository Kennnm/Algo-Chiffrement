const socket = io("http://127.0.0.1:5000");
let clientPrivateKey, clientPublicKey, serverPublicKey;


// Écouter la liste des utilisateurs connectés dès l'ouverture de la page
socket.on("connect", () => {
    socket.emit("get_users"); // Demande la liste des utilisateurs dès connexion au serveur
});

// Charger la clé privée au démarrage
let clientPrivateKeyPem = sessionStorage.getItem("privateKey");
if (clientPrivateKeyPem) {
    try {
        clientPrivateKey = forge.pki.privateKeyFromPem(clientPrivateKeyPem);
    } catch (error) {
        console.error("Erreur lors de la récupération de la clé privée :", error);
    }
} else {
    console.warn("Aucune clé privée trouvée au démarrage !");
}


// Fonction pour générer la paire de clés RSA côté client
async function generateRSAKeys() {
    return new Promise((resolve) => {
        const keyPair = forge.pki.rsa.generateKeyPair({ bits: 2048 });

        // Convertir les clés en PEM
        const privateKeyPem = forge.pki.privateKeyToPem(keyPair.privateKey);
        const publicKeyPem = forge.pki.publicKeyToPem(keyPair.publicKey);

        // Stocker la clé privée dans sesssionStorage
        sessionStorage.setItem("privateKey", privateKeyPem);
        sessionStorage.setItem("publicKey", publicKeyPem);
        clientPrivateKey = keyPair.privateKey;

        resolve(publicKeyPem); // Retourne la clé publique
    });
}

async function getRecipientPublicKey(recipient) {
    const response = await fetch(`http://127.0.0.1:5000/get_public_key/${recipient}`);
    const data = await response.json();
    
    if (data.error) {
        console.error("Erreur : Clé publique non trouvée pour", recipient);
        return null;
    }

    const publicKeyPem = atob(data.public_key);
    return forge.pki.publicKeyFromPem(atob(data.public_key));
}


// Gestion de la connexion d'un utilisateur
async function login() {
    const username = document.getElementById("username").value;
    if (username) {
        const publicKey = await generateRSAKeys(); // Générer une clé publique RSA
        socket.emit("register", { username, public_key: publicKey });
        socket.emit("get_users");

        document.querySelector(".login-form").style.display = "none";
        document.querySelector(".message-form").style.display = "block";
    }
}

socket.on("liste_utilisateurs", (usersList) => {
    const username = document.getElementById("username")?.value || "";
    const userList = document.getElementById("user-list");
    userList.innerHTML = "";
    
    usersList.forEach(user => {
        if (user !== username) { // Ne pas afficher l'utilisateur lui-même
            const li = document.createElement("li");
            li.textContent = user;
            
            li.addEventListener("click", function() {
                document.getElementById("recipient").value = user; // Sélectionne un destinataire
                document.querySelectorAll(".sidebar ul li").forEach(li => li.classList.remove("selected"));
                this.classList.add("selected");
            });
            
            userList.appendChild(li);
        }
    });
});


// Met à jour la liste lorsqu'un utilisateur se connecte ou se déconnecte
socket.on("user_update", () => {
    socket.emit("get_users");
});


// Fonction pour déchiffrer avec la clé privée du client
async function decryptRSAWithPrivateKey(encryptedData) {
    const privateKey = await window.crypto.subtle.importKey(
        "pkcs8",
        clientPrivateKey,  // Ta clé privée RSA stockée au chargement
        {
            name: "RSA-OAEP",
            hash: "SHA-256"
        },
        false,
        ["decrypt"]
    );

    let decrypted = await window.crypto.subtle.decrypt(
        { name: "RSA-OAEP" },
        privateKey,
        encryptedData
    );

    return new TextDecoder().decode(decrypted);
}

// Chiffrer un message avec AES
function encryptAES(message, aesKey) {
    const iv = forge.random.getBytesSync(16);
    const cipher = forge.cipher.createCipher("AES-CBC", aesKey);
    cipher.start({ iv });
    cipher.update(forge.util.createBuffer(message, "utf8"));
    cipher.finish();
    return {
        encrypted: forge.util.encode64(cipher.output.getBytes()),
        iv: forge.util.encode64(iv),
    };
}

// Déchiffrer un message avec AES
function decryptAES(encrypted, key, iv) {
    const decipher = forge.cipher.createDecipher("AES-CBC", key);
    decipher.start({ iv: forge.util.decode64(iv) });
    decipher.update(forge.util.createBuffer(forge.util.decode64(encrypted)));
    decipher.finish();
    return decipher.output.toString();
}

// Déchiffrer la clé AES avec RSA (clé privée du client)
function decryptAESKeyWithRSA(encryptedKey) {

    let privateKeyPem = sessionStorage.getItem("privateKey");

    if (!privateKeyPem) {
        console.error("Aucune clé privée trouvée dans sessionStorage !");
        return null;
    }

    if (!clientPrivateKey) {
        clientPrivateKey = forge.pki.privateKeyFromPem(privateKeyPem);
    }

    try {
        const decryptedKey = clientPrivateKey.decrypt(forge.util.decode64(encryptedKey), "RSA-OAEP");
        return decryptedKey;
    } catch (error) {
        console.error("Erreur lors du déchiffrement de la clé AES :", error);
        return null;
    }
}


// Envoyer un message chiffré
async function sendMessage() {
    const username = document.getElementById("username").value;
    const recipient = document.getElementById("recipient").value;
    const message = document.getElementById("message").value;

    if (!recipient || !message) {
        return alert("Sélectionnez un destinataire et entrez un message.");
    }

    // Récupérer la clé publique du destinataire
    const recipientPublicKey = await getRecipientPublicKey(recipient);
    if (!recipientPublicKey) {
        return alert("Impossible de récupérer la clé publique du destinataire.");
    }

    const aesKey = forge.random.getBytesSync(16); // Générer une clé AES aléatoire
    const encryptedAESKey = forge.util.encode64(recipientPublicKey.encrypt(aesKey, "RSA-OAEP")); // Chiffrer avec la clé du destinataire
    
    let publicKeyPem = sessionStorage.getItem("publicKey"); // Récupérer la clé publique du client (sois-même)	
    var clientPublicKey = forge.pki.publicKeyFromPem(publicKeyPem);
    const encryptedAESKeyForSender = forge.util.encode64(clientPublicKey.encrypt(aesKey, "RSA-OAEP"));


    const { encrypted, iv } = encryptAES(message, aesKey); // Chiffrer le message avec AES

    socket.emit("send_message", {
        sender: username,
        recipient,
        encrypted_aes_key: encryptedAESKey,
        encrypted_aes_key_for_sender: encryptedAESKeyForSender,
        iv,
        message: encrypted,
    });

    document.getElementById("message").value = "";
}


// Déchiffrer un message reçu
socket.on("receive_message", (data) => {
    const { sender, encrypted_aes_key, encrypted_aes_key_for_sender, iv, message } = data;
    const currentUser = document.getElementById("username").value;
    let decryptedAESKey = null;

    // Vérification : choisir la bonne clé AES en fonction de l'utilisateur
    if (currentUser === sender) {
        decryptedAESKey = decryptAESKeyWithRSA(encrypted_aes_key_for_sender);
    } else {
        decryptedAESKey = decryptAESKeyWithRSA(encrypted_aes_key);
    }

    if (!decryptedAESKey) {
        console.warn("Impossible de déchiffrer la clé AES. Ce message n'est peut-être pas destiné à ce client.");
        return;
    }

    // Déchiffrement du message
    const decryptedMessage = decryptAES(message, decryptedAESKey, iv);

    // Création de l'élément message
    const li = document.createElement("li");

    // Ajout du nom de l'expéditeur
    const senderName = document.createElement("span");
    senderName.textContent = sender === currentUser ? "Moi" : sender;
    senderName.classList.add("message-sender");

    // Ajout du texte du message
    const messageText = document.createElement("p");
    messageText.textContent = decryptedMessage;

    // Affichage : l'expéditeur est à gauche, le destinataire à droite
    if (sender === currentUser) {
        li.classList.add("message-received"); // Expéditeur → Gauche
    } else {
        li.classList.add("message-sent"); // Destinataire → Droite
    }

    // Ajout des éléments au message
    li.appendChild(senderName);
    li.appendChild(messageText);

    document.getElementById("messages").appendChild(li);
});







