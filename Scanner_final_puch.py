import sqlite3
from getmac import get_mac_address
import socket
import ipaddress
import netifaces
import scapy.all as scapy
from typing import Tuple, Optional, Dict
import psutil  # module(pour monitorer le systeme) qui fait comme ps, top, lsof, netstat, ifconfig, who, df, kill, free, nice, ionice, iostat, iotop, uptime, pidof, tty, taskset, pmap
import threading


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

if __name__ == "__main__":

    resultat = get_active_interface()
    if resultat:
        interface, ip, masque = resultat
        print(f"Votre Adresse Réseau: {get_network_address()}")
        print(f"Votre Interface Active: {interface}")
        print(f"Votre Adresse IP: {ip}")
        print(f"Votre Masque Réseau: {masque}")
        print(f"Votre MAC Adresse: {get_mac()}")
        # analyser_reseau(get_network_address())
    else:
        print("Aucune i nterface active trouvée")