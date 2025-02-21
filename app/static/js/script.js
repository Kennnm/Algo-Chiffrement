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

// Réception de messages
socket.on("message_recu", (data) => {
    let msgList = document.getElementById("messages");
    let li = document.createElement("li");
    li.innerText = `${data.expediteur}: ${data.message}`;
    msgList.appendChild(li);
});
