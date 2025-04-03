
import socket
import ipaddress
import get_ip_mask_interface
import scapy.all as scapy
from typing import Tuple, Optional, Dict
import psutil  # module(pour monitorer le systeme) qui fait comme ps, top, lsof, netstat, ifconfig, who, df, kill, free, nice, ionice, iostat, iotop, uptime, pidof, tty, taskset, pmap
from getmac import get_mac_address
import time
import socket
import ipaddress
import nmap


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
    network_info = get_ip_mask_interface.get_interface_info()
    if network_info:
        active_interface = network_info['interface']
        ip = network_info['ip'] 
        netmask = network_info['subnet_mask']
        return (active_interface, ip, netmask)
    else:
        print("Error with get actove interface")
        return (None, None, None)
        
       

    

def get_mac():
    mac_address = get_mac_address()
    return mac_address
def scan_ports(ip, ports):
    nm = nmap.PortScanner()  # Création d'un objet scanner nmap
    open_ports = {}  # Dictionnaire pour stocker les ports ouverts
    
    # Scanner les ports spécifiés en une seule fois
    ports_str = ",".join(map(str, ports))  # Conversion de la liste des ports en une chaîne de caractères
    
    try:
        # Lancer le scan pour les ports spécifiés en utilisant l'option -T4 pour un scan plus rapide
        nm.scan(ip, ports_str, arguments='-T4')

        # Vérifier chaque port
        for port in ports:
            # Vérifier si le port est ouvert
            if nm[ip].has_tcp(port) and nm[ip].tcp(port)['state'] == 'open':
                # Obtenir le nom du service, si disponible, sinon "Unknown"
                service_name = nm[ip].tcp(port).get('name', 'Unknown')
                open_ports[port] = service_name

    except Exception as e:
        print(f"Erreur lors du scan : {e}")  # Gérer les erreurs de scan
    
    return open_ports  # Retourner les ports ouverts

# def scan_ports(ip, ports):
#     open_ports = {}
#     for port in ports:
#         sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#         sock.settimeout(0.1)  # timeout pour la connection
#         result = sock.connect_ex((ip, port))
#         if result == 0:
#             open_ports[port] = SERVICE_DICT.get(port, "Unknown")
#         sock.close()
#     return open_ports 

def analyser_reseau(ip_avec_masque):
    try:
        # Analyser l'adresse IP avec le masque
        reseau = ipaddress.IPv4Network(ip_avec_masque, strict=False)
        print(f"\n[INFO] Réseau détecté: {reseau}\n")

        while True:  
            # mise-a-joir de liste IP
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
            
            resultat = get_active_interface()
            interface, ip, masque = resultat

            print(f"Votre Adresse Réseau: {get_network_address()}")
            print(f"Votre Adresse IP: {ip}")
            print(f"Votre Masque Réseau: {masque}")
            print(f"Votre MAC Adresse: {get_mac()}")

            print(f"Appareils trouvés dans le réseau {reseau}:")
            print("-" * 80)
            print(f"{'IP':<20} {'MAC':<20} {'Nostname':<30} {'Ports ouverts':<50}")
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

                # Scan des ports
                open_ports = scan_ports(recu.psrc, SERVICE_DICT.keys())
                ports_info = ", ".join([f"{port} ({service})" for port, service in open_ports.items()])

                # Affichage des informations sur chaque hôte
                print(f"{recu.psrc:<20} {recu.hwsrc:<20} {nom_hote:<30} {ports_info:<50}")
                compteur_hotes += 1

            # Affichage du nombre total d'hôtes
            print("-" * 80)
            print(f"[INFO] Nombre total d'hôtes trouvés: {compteur_hotes}")
            
            # Pour etre comme wifith 
            time.sleep(2)

    except Exception as e:
        print(f"[ERREUR] {e}")

# ex d utilisation 
# analyser_reseau("192.168.1.0/24")
SERVICE_DICT = {
    21: "FTP",  # File Transfer Protocol
    22: "SSH",  # Secure Shell
    23: "Telnet",  # Telnet protocol
    25: "SMTP",  # Simple Mail Transfer Protocol
    53: "DNS",  # Domain Name System
    69: "TFTP",  # Trivial File Transfer Protocol
    80: "HTTP",  # Hypertext Transfer Protocol
    443: "HTTPS",  # Hypertext Transfer Protocol Secure
    110: "POP3",  # Post Office Protocol 3
    143: "IMAP",  # Internet Message Access Protocol
    3306: "MySQL",  # MySQL Database
    3389: "RDP",  # Remote Desktop Protocol
    8080: "HTTP Proxy",  # Alternative HTTP port (Proxy)
    8888: "HTTP Alternative",  # Alternative HTTP port
    3307: "MySQL Cluster",  # MySQL Cluster
    8000: "HTTP (Python Simple Server)",  # Python HTTP server (default port)
    5000: "Flask / HTTP API",  # Flask web framework default port
    5432: "PostgreSQL",  # PostgreSQL Database
    6379: "Redis",  # Redis key-value store
    9200: "Elasticsearch",  # Elasticsearch service
    9300: "Elasticsearch (transport)",  # Elasticsearch transport port
    27017: "MongoDB",  # MongoDB Database
    161: "SNMP",  # Simple Network Management Protocol
    162: "SNMP Trap",  # SNMP Trap
    514: "Syslog",  # Syslog service
    520: "RIP",  # Routing Information Protocol
    631: "CUPS",  # Common UNIX Printing System (CUPS)
    3128: "Squid Proxy",  # Squid Proxy Server
    4444: "Blaster Worm",  # Blaster Worm (malicious software)
    5555: "Android Debug Bridge (ADB)",  # Android Debug Bridge
    5900: "VNC",  # Virtual Network Computing (VNC)
    6000: "X11",  # X Window System
    6660: "IRC",  # Internet Relay Chat
    6667: "IRC",  # Internet Relay Chat (default port)
    1080: "SOCKS Proxy",  # SOCKS Proxy
    1433: "Microsoft SQL Server",  # Microsoft SQL Server
    1434: "Microsoft SQL Server (SQL Resolution)",  # Microsoft SQL Server Resolution
    1521: "Oracle Database",  # Oracle Database
    2049: "NFS",  # Network File System
    3690: "Subversion (SVN)",  # Subversion version control
    5060: "SIP",  # Session Initiation Protocol
    8081: "HTTP Proxy",  # HTTP Proxy Alternative
    9090: "Webmin",  # Webmin service
    9999: "Remote Administration",  # Remote Administration (e.g., Netcat)
    10000: "Webmin",  # Webmin service (default port)
    20000: "Webmin",  # Webmin (Alternative port)
    10051: "Zabbix agent",  # Zabbix monitoring agent
    12345: "NetBus Trojan",  # NetBus Trojan (malicious software)
    31337: "Back Orifice",  # Back Orifice (malicious software)
    44444: "Blaster Worm",  # Blaster Worm (malicious software)
    55555: "Netcat",  # Netcat (network tool)
    6666: "Localhost service",  # Localhost service (possibly malicious)
    1234: "C&C service",  # Command and Control (malicious service)
    4321: "DDoS botnet (agent)",  # DDoS botnet agent
    8009: "Tomcat AJP",  # Tomcat AJP (Apache JServ Protocol)
    8888: "HTTP (alternative)",  # HTTP alternative port
}


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