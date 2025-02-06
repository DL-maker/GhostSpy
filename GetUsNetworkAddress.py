
from getmac import get_mac_address
import socket
import ipaddress
import netifaces
import scapy.all as scapy
from typing import Tuple, Optional, Dict
import psutil

def get_network_address():
    # Получаем все сетевые интерфейсы
    for interface, addrs in psutil.net_if_addrs().items():
        for addr in addrs:
            # Пропускаем интерфейс loopback (lo)
            if addr.family == 2:  # IPv4
                if interface != 'lo':  # Убедимся, что это не интерфейс lo
                    ip = addr.address
                    netmask = None
                    # Ищем соответствующую маску подсети
                    for mask in addrs:
                        if mask.family == 2:  # IPv4 маска
                            netmask = mask.netmask
                            break

                    if netmask:
                        # Формируем строку типа "IP/маска" для вычисления сети
                        network = ipaddress.IPv4Network(f"{ip}/{netmask}", strict=False)

                        # Возвращаем сетевой адрес в формате IP/маска
                        return f"{network.network_address}/{network.prefixlen}"

    return None
def get_active_interface() -> tuple[str, str, str]:
    """
    Renvoie le nom de l'interface active, son adresse IP et son masque réseau.

    Returns:
        tuple[str, str, str]: (Nom de l'interface, Adresse IP, masque réseau)
    """
    try:
        # Obtenir les informations de la passerelle par défaut
        gateways = netifaces.gateways()
        if 'default' not in gateways or netifaces.AF_INET not in gateways['default']:
            return None

        # Obtenir l'interface active
        active_interface = gateways['default'][netifaces.AF_INET][1]

        # Obtenir les adresses pour cette interface
        addrs = netifaces.ifaddresses(active_interface)

        # Vérifier la présence d'une adresse IPv4
        if netifaces.AF_INET in addrs:
            ip_info = addrs[netifaces.AF_INET][0]
            ip = ip_info.get('addr')
            netmask = ip_info.get('netmask')

            # Ne retourner que si l'IP est valide et non loopback
            if ip and netmask and ip != '127.0.0.1':
                return (active_interface, ip, netmask)

        return None

    except Exception as e:
        print(f"Erreur lors de la récupération des informations réseau: {e}")
        return None

def get_mac():
    mac_address = get_mac_address()
    return mac_address
def analyser_reseau(ip_avec_masque):
    try:
        # Analyser l'adresse IP avec le masque
        reseau = ipaddress.IPv4Network(ip_avec_masque, strict=False)
        print(f"\n[INFO] Réseau détecté: {reseau}\n")

        # Obtenir la plage d'adresses IP
        ips = [str(ip) for ip in reseau.hosts()]

        # Requête ARP
        requete_arp = scapy.ARP(pdst=ips)
        diffusion = scapy.Ether(dst="ff:ff:ff:ff:ff:ff")
        requete_arp_diffusion = diffusion / requete_arp

        # Temps d'attente minimal
        reponses = scapy.srp(requete_arp_diffusion, timeout=0.5, verbose=False)[0]

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

    except Exception as e:
        print(f"[ERREUR] {e}")
if __name__ == "__main__":
    resultat = get_active_interface()
    if resultat:
        interface, ip, masque = resultat
        print(f"votre Adreese réseau: {get_network_address()}")
        print(f"votre Interface active: {interface}")
        print(f"votre Adresse IP: {ip}")
        print(f"votre Masque réseau: {masque}")
        print(f"votre mac adresse{get_mac()}")
        analyser_reseau(get_network_address())
    else:
        print("Aucune interface active trouvée")



