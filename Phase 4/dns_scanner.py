from scapy.all import *
import dns.resolver
import tkinter as tk
# import winsound  # For playing a sound on Windows
import pygame  # For playing a sound cross-platform

# Ensemble pour stocker les domaines qui ont déjà été traités
processed_domains = set()

# Liste des domaines à surveiller
watched_domains = ["wikipedia.com", "instagram.com"]

# Fonction pour envoyer une alerte avec fenêtre et son
def alert_if_watched(domain_name):
    if any(watched_domain in domain_name for watched_domain in watched_domains):
        # Afficher l'alerte sous forme de fenêtre
        show_alert(domain_name)
        # Jouer un son (sur Windows)
        # play_ping_sound()

# Fonction pour afficher une fenêtre d'alerte
def show_alert(domain_name):
    root = tk.Tk()
    root.title("Alerte de Domaine Visité")
    
    # Message dans la fenêtre
    message = f"Le domaine visité est surveillé: {domain_name}"
    label = tk.Label(root, text=message, padx=20, pady=20)
    label.pack()

    # Bouton pour fermer l'alerte
    close_button = tk.Button(root, text="Fermer", command=root.destroy)
    close_button.pack(pady=10)

    # Afficher la fenêtre
    root.mainloop()

# Fonction pour jouer un son de type "ping
# def play_ping_sound():
#     try:
#         # Pour Windows
#         winsound.Beep(2000, 500)  # 1000 Hz pendant 500 ms MARCHE
#     except:
#         # Si ce n'est pas Windows, utiliser pygame pour le son MARCHE PASSSSS
#         pygame.mixer.init()
#         pygame.mixer.Sound("ping_sound.wav").play()

# Fonction pour traiter chaque paquet
def packet_printer(packet):
    if packet.haslayer(DNS) and packet[DNS].qr == 0:  # Vérifie que c'est une requête DNS (qr == 0)
        src_ip = packet[IP].src  # Obtient l'adresse IP de l'expéditeur
        if packet.haslayer(DNSQR):  # Si c'est une requête DNS
            domain_name = packet[DNSQR].qname.decode()  # Obtient le nom de domaine de la requête
            
            # Si le domaine a déjà été traité, on le saute
            if domain_name in processed_domains:
                return
            
            # Ajoute le domaine à l'ensemble des domaines traités
            processed_domains.add(domain_name)
            
            # Vérifier si le domaine est dans la liste des domaines surveillés
            alert_if_watched(domain_name)
            
            try:
                # Utilise le serveur DNS pour résoudre le nom de domaine en adresse IP
                answer = dns.resolver.resolve(domain_name, 'A')  # 'A' pour les adresses IPv4
                resource_ip = answer[0].to_text()  # Obtient l'adresse IP de la ressource
                print(f"IP source: {src_ip} -> Domaine: {domain_name} -> IP de la ressource: {resource_ip}")
            except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN, dns.resolver.Timeout):
                # Si la résolution du domaine échoue, affiche seulement le nom du domaine
                print(f"IP source: {src_ip} -> Domaine: {domain_name} -> IP de la ressource: N/A (impossible de résoudre)")

# Capture de paquets en mode promiscuité (pour les réseaux câblés)
# On active le sniffing sur l'interface (indiquez votre interface, par exemple "eth0" ou "wlan0")
# Pour le Wi-Fi : utilisez le mode surveillance avec l'interface correspondante, par exemple "wlan0mon"

iface = "wlan0"  # Indiquez votre interface, par exemple "wlan0" pour le Wi-Fi ou "eth0" pour un réseau câblé
print(f"Début de la capture des requêtes DNS sur l'interface {iface}...")

# Capture des requêtes DNS
sniff(iface=iface, prn=packet_printer, filter="udp port 53", store=0)
