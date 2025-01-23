
import psutil
import ipaddress
from scapy.all import ARP, Ether, srp, conf
from scapy.all import ARP, Ether, srp
import socket
import struct
import fcntl
import os
import psutil
import socket
from getmac import get_mac_address
import socket

import netifaces
from typing import Tuple, Optional, Dict

from GetHostName import hosts


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
                        # Вычисляем сетевой адрес
                        network = ipaddress.IPv4Network(f"{ip}/{netmask}", strict=False)
                        return network.network_address

    return None


network_address = get_network_address()
if network_address:
    print(f"Network address: {network_address}")
    network = network_address

else:
    print("No network address found.")




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
# Exemple d'utilisation
resultat = get_active_interface()
if resultat:
    interface, ip, masque = resultat
    print(f"Interface active: {interface}")
    print(f"Adresse IP: {ip}")
    print(f"Masque réseau: {masque}")
    print(get_mac())
else:
    print("Aucune interface active trouvée")






def generate_ips_in_range(network_ip, subnet_mask):
    ip_parts = struct.unpack('!I', socket.inet_aton(network_ip))[0]
    mask_parts = struct.unpack('!I', socket.inet_aton(subnet_mask))[0]

    # Calculer l'adresse du réseau
    network = ip_parts & mask_parts

    # Calculer le nombre d'adresses IP disponibles dans le réseau
    num_ips = 2 ** (32 - bin(mask_parts).count('1')) - 2  # exclure l'adresse réseau et l'adresse de broadcast

    ips = []
    for i in range(1, num_ips + 1):
        ip = socket.inet_ntoa(struct.pack('!I', network + i))
        ips.append(ip)

    return ips


# Fonction pour scanner les hôtes dans un réseau donné
def scan_network(target_ips):
    hosts = []

    for ip in target_ips:
        arp_request = ARP(pdst=ip)
        broadcast = Ether(dst="ff:ff:ff:ff:ff:ff")  # Cadre Ethernet pour la diffusion
        arp_request_broadcast = broadcast / arp_request

        # Envoyer la requête ARP et obtenir les réponses
        answered_list = srp(arp_request_broadcast, timeout=1, verbose=False, iface="wlp0s20f3")[0]

        # Ajouter les hôtes répondus à la liste
        for element in answered_list:
            host = {
                "ip": element[1].psrc,
                "mac": element[1].hwsrc
            }
            hosts.append(host)

    return hosts


# Fonction pour afficher les résultats
def print_results(hosts, my_ip, my_mac):
    print("\nRésultats du scan réseau:")
    print("IP-Adresse\t\tAdresse MAC")
    print("-" * 40)

    # Afficher votre propre IP et MAC
    print(f"\n{my_ip}\t\t{my_mac}")

    # Afficher les résultats des autres hôtes
    for host in hosts:
        print(f"{host['ip']}\t\t{host['mac']}")


def main():
    # Définir l'interface réseau que vous utilisez (par exemple, "wlp0s20f3")
    interface = "wlp0s20f3"

    # Obtenez votre propre IP et MAC et INterface
    result = get_active_interface()
    interfacee, ipa, masquee = resultat
    my_mac = get_mac()

    # Spécifiez l'IP et le masque de sous-réseau (ajustez en fonction de votre configuration réseau)
    ip = ipa # L'IP de votre machine
    subnet_mask = masquee  # Masque de sous-réseau /28 (ex. 172.20.10.0/28)

    # Générer la liste des IPs dans la plage
    target_ips = generate_ips_in_range(ip, subnet_mask)

    # Afficher les résultats du scan
    print(f"Plage pour le scan: {target_ips[0]} - {target_ips[-1]}")

    # Scanner le réseau
    hosts = scan_network(target_ips)

    # Afficher les résultats
    print_results(hosts, ipa, my_mac)
    # listofIPHOST = []
    # listofIPHOST += hosts
    # listofIPHOST += [{"ip":ipa}]
    # for i in range (len(list(listofIPHOST))):
    #     print(listofIPHOST[i]['ip'])

if __name__ == "__main__":
    main()



