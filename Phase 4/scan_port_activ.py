# On importe la bibliothèque psutil qui nous permet de récupérer des informations sur les connexions réseau
import psutil

# Fonction qui permet de récupérer les ports ouverts sur l'ordinateur
def get_open_ports():
    # On initialise un ensemble (set) pour stocker les ports ouverts
    open_ports = set()
    
    # On récupère toutes les connexions réseau qui sont de type 'inet' (connexions Internet)
    # On spécifie 'kind="inet"' pour obtenir les connexions TCP/IP
    for conn in psutil.net_connections(kind='inet'):
        # On ne garde que les connexions qui ont le statut 'LISTEN' (écoutent sur un port)
        if conn.status == 'LISTEN':
            # Si le port est en mode 'LISTEN', on l'ajoute à l'ensemble open_ports
            open_ports.add(conn.laddr.port)  # conn.laddr.port contient le numéro du port
    
    # On retourne l'ensemble des ports ouverts
    return open_ports

# Fonction principale qui va exécuter le code
def main():
    # On récupère les ports ouverts en appelant la fonction get_open_ports
    open_ports = get_open_ports()

    # On affiche un message indiquant les ports ouverts
    print("Voici les ports ouverts :")
    
    # Si la liste des ports ouverts n'est pas vide, on les affiche
    if open_ports:
        # On affiche chaque port dans l'ensemble open_ports (en les triant pour plus de clarté)
        for port in sorted(open_ports):
            print(port)
    else:
        # Si aucun port n'est ouvert, on affiche ce message
        print("Aucun port ouvert.")

# Si le fichier est exécuté directement (plutôt qu'importé comme module), la fonction main est appelée
if __name__ == "__main__":
    main()
