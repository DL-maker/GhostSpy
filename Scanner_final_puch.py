import sqlite3
from getmac import get_mac_address
import socket
import ipaddress
import netifaces
import scapy.all as scapy
from typing import Tuple, Optional, Dict
import psutil  # module(pour monitorer le systeme) qui fait comme ps, top, lsof, netstat, ifconfig, who, df, kill, free, nice, ionice, iostat, iotop, uptime, pidof, tty, taskset, pmap
import threading
import time
import socket
import ipaddress


def get_network_address():
    for interface, addrs in psutil.net_if_addrs().items():
        for addr in addrs:
            if addr.family == 2:  # IPv4
                if interface != 'lo':
                    ip = addr.address
                    netmask = None
                    for mask in addrs:
                        if mask.family == 2:
                            netmask = mask.netmask
                            break

                    if netmask:
                        network = ipaddress.IPv4Network(f"{ip}/{netmask}", strict=False)
                        return f"{network.network_address}/{network.prefixlen}"

    return None

def get_active_interface() -> tuple:
    try:
        gateways = netifaces.gateways()
        if 'default' not in gateways or netifaces.AF_INET not in gateways['default']:
            return None

        active_interface = gateways['default'][netifaces.AF_INET][1]
        addrs = netifaces.ifaddresses(active_interface)

        if netifaces.AF_INET in addrs:
            ip_info = addrs[netifaces.AF_INET][0]
            ip = ip_info.get('addr')
            netmask = ip_info.get('netmask')

            if ip and netmask and ip != '127.0.0.1':
                return (active_interface, ip, netmask)

        return None

    except Exception as e:
        print(f"Erreur: {e}")
        return None


def get_mac():
    mac_address = get_mac_address()
    return mac_address
def analyser_reseau(ip_avec_masque):
    try:
        # Analyser l'adresse IP avec le masque
        reseau = ipaddress.IPv4Network(ip_avec_masque, strict=False)
        print(f"\n[INFO] Réseau détecté: {reseau}\n")

        while True:  
            # Обновление списка IP-адресов в сети
            ips = [str(ip) for ip in reseau.hosts()]

            # Requête ARP
            requete_arp = scapy.ARP(pdst=ips)
            diffusion = scapy.Ether(dst="ff:ff:ff:ff:ff:ff")
            requete_arp_diffusion = diffusion / requete_arp

            # Temps d'attente minimal
            reponses = scapy.srp(requete_arp_diffusion, timeout=2, verbose=False)[0]

            # beau print
            print("\033c", end="")

            # Affichage de l'entête
            print(f"Appareils trouvés dans le réseau {reseau}:")
            print("-" * 80)
            print(f"{'IP':<20} {'MAC':<20} {'Nom d\'hôte':<30}")
            print("-" * 80)

            # Compteur pour le nombre total d'hôtes
            compteur_hotes = 0

            # Affichage des résultats
            for envoye, recu in reponses:
                try:
                    # Tente de résoudre le nom d'hôte
                    nom_hote = socket.gethostbyaddr(recu.psrc)[0]
                except (socket.herror, socket.gaierror):
                    # Si le nom d'hôte n'est pas trouvé, afficher une valeur par défaut
                    nom_hote = "Inconnu"

                # Affichage des informations sur chaque hôte
                print(f"{recu.psrc:<20} {recu.hwsrc:<20} {nom_hote:<30}")
                compteur_hotes += 1

            # Affichage du nombre total d'hôtes
            print("-" * 80)
            print(f"[INFO] Nombre total d'hôtes trouvés: {compteur_hotes}")
            
            # Pour etre comme wifith 
            time.sleep(2)

    except Exception as e:
        print(f"[ERREUR] {e}")

# Пример вызова функции
# analyser_reseau("192.168.1.0/24")


if __name__ == "__main__":

    resultat = get_active_interface()
    if resultat:
        interface, ip, masque = resultat
        print(f"Votre Adresse Réseau: {get_network_address()}")
        print(f"Votre Interface Active: {interface}")
        print(f"Votre Adresse IP: {ip}")
        print(f"Votre Masque Réseau: {masque}")
        print(f"Votre MAC Adresse: {get_mac()}")
        analyser_reseau(get_network_address())
    else:
        print("Aucune i nterface active trouvée")