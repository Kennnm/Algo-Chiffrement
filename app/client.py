import socket # Gère les connexions par socket 

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as connexion_serveur: # Crée un socket pour écouter les connexions
    connexion_serveur.connect(('localhost', 1234)) # Se connecte au serveur localhost:1234
    print('Connecté au serveur localhost:1234') # Affiche un message de confirmation
    connexion_serveur.send(b'Bonjour serveur !') # Ce que le client envoie au serveur
    print('Message envoyé au serveur') # Affiche un message de confirmation
    
    
connexion_serveur.close() # Ferme la connexion