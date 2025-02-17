import socket # Gère les connexions par socket 

connexion_serveur = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # Crée un socket pour se connecter à un serveur
connexion_serveur.connect(('localhost', 1234)) # Se connecte au serveur localhost:1234  
print('Connecté au serveur localhost:1234')

connexion_serveur.send(b'Bonjour serveur !') # Ce que le client envoie au serveur

connexion_serveur.close() # Ferme la connexion