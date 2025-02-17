import socket # Gère les connexions par socket

nom_hote = 'localhost' # Nom d'hôte du serveur
port_ecoute = 1234 # Port d'écoute du serveur

    
socket_ecoute = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # Crée un socket pour écouter les connexions

socket_ecoute.bind((nom_hote, port_ecoute)) # Associe le socket à l'adresse localhost:1234
socket_ecoute.listen(5) # Commence à écouter les connexions entrantes avec 5 connexions en attente maximum
print('Serveur démarré sur localhost:1234')

connexion_client, adresse_client = socket_ecoute.accept() # Accepte une connexion entrante
print('Connexion reçue de', adresse_client) # Affiche l'adresse de l'expéditeur de la connexion 

message = connexion_client.recv(1024) # Création de variable et stocke le message reçu par le client
print(message) # Affiche lemessage

connexion_client.close()
socket_ecoute.close() # Ferme le socket d'écoute