import subprocess
import platform
import re
import psutil

def get_active_internet_interface():
    """
    Détermine l'interface active connectée à Internet
    Retourne le nom de l'interface active ou None si aucune connexion active n'est trouvée
    """
    try:
        # Vérifie toutes les interfaces avec psutil
        net_if_addrs = psutil.net_if_addrs()
        net_if_stats = psutil.net_if_stats()
        
        # Vérifie d'abord les connexions filaires, puis sans fil (priorité Ethernet)
        ethernet_interfaces = []
        wifi_interfaces = []
        
        for interface, stats in net_if_stats.items():
            # Ignore les interfaces désactivées et le loopback local
            if not stats.isup or interface.lower() == 'lo' or 'loopback' in interface.lower():
                continue
                
            # Vérifie la présence d'une adresse IP (sauf localhost)
            has_valid_ip = False
            if interface in net_if_addrs:
                for addr in net_if_addrs[interface]:
                    # Vérifie uniquement les adresses IPv4 (AF_INET = 2 pour IPv4)
                    if addr.family == 2 and addr.address != '127.0.0.1':
                        has_valid_ip = True
                        break
                        
            if not has_valid_ip:
                continue
                
            # Si l'interface est active et a une IP, l'ajouter à la liste correspondante
            if any(eth_id in interface.lower() for eth_id in ['eth', 'en', 'eno', 'enp']):
                ethernet_interfaces.append(interface)
            elif any(wifi_id in interface.lower() for wifi_id in ['wlan', 'wi-fi', 'wireless', 'wl', 'wifi']):
                wifi_interfaces.append(interface)
        
        # Retourne l'interface selon la priorité : d'abord Ethernet, puis Wi-Fi
        if ethernet_interfaces:
            return ethernet_interfaces[0]
        elif wifi_interfaces:
            return wifi_interfaces[0]
            
        return None
    except Exception as e:
        print(f"Erreur lors de la détection de l'interface active : {e}")
        return None

def get_network_info(interface):
    """Récupère les informations réseau de l'interface spécifiée"""
    try:
        if platform.system() == 'Windows':
            # Utilisation de ipconfig pour Windows au lieu de wmic
            result = subprocess.check_output(['ipconfig', '/all'], shell=True).decode('cp1252', errors='ignore')
            
            info = {
                'ip': None,
                'subnet_mask': None
            }
            
            # Trouver les sections spécifiques à l'interface
            sections = result.split('\n\n')
            for section in sections:
                if interface.lower() in section.lower():
                    # Rechercher l'adresse IPv4
                    ip_match = re.search(r'IPv4.+?:\s+(\d+\.\d+\.\d+\.\d+)', section)
                    mask_match = re.search(r'Subnet Mask.+?:\s+(\d+\.\d+\.\d+\.\d+)', section)
                    
                    if ip_match:
                        info['ip'] = ip_match.group(1)
                    if mask_match:
                        info['subnet_mask'] = mask_match.group(1)
                    
                    # Si on a trouvé les informations, on sort de la boucle
                    if info['ip'] and info['subnet_mask']:
                        break
        else:
            result = subprocess.check_output([
                'ip', 'addr', 'show', interface
            ]).decode(errors='ignore').strip()
            
            info = {
                'ip': None,
                'subnet_mask': '255.255.255.0'  # Masque par défaut standard
            }
            
            for line in result.split('\n'):
                if 'inet ' in line:
                    parts = line.split()
                    if len(parts) > 1:
                        # Extrait l'adresse IP et le préfixe CIDR
                        ip_with_cidr = parts[1]
                        if '/' in ip_with_cidr:
                            info['ip'] = ip_with_cidr.split('/')[0]
                            # Convertit le préfixe CIDR en masque de sous-réseau
                            cidr = int(ip_with_cidr.split('/')[1])
                            info['subnet_mask'] = cidr_to_netmask(cidr)
                        else:
                            info['ip'] = ip_with_cidr
        
        return info
    except Exception as e:
        print(f"Erreur lors de la récupération des informations réseau pour {interface} : {e}")
        return None

def cidr_to_netmask(cidr):
    """Convertit un préfixe CIDR en masque de sous-réseau"""
    binary = ('1' * cidr).ljust(32, '0')
    octets = [binary[i:i+8] for i in range(0, 32, 8)]
    return '.'.join(str(int(octet, 2)) for octet in octets)

def get_interface_info():
    """
    Retourne un dictionnaire avec les informations sur l'interface réseau active :
    - nom de l'interface
    - adresse IP
    - masque de sous-réseau
    - type de connexion (Wi-Fi ou Ethernet)
    """
    try:
        # Récupère l'interface active
        active_interface = get_active_internet_interface()
        
        if not active_interface:
            return None
            
        # Récupère les informations sur l'interface
        if platform.system() == 'Windows':
            # Pour Windows, on utilise directement le nom de l'interface avec la nouvelle fonction
            info = get_network_info(active_interface)
        else:
            # Pour Linux, utilise directement le nom de l'interface
            info = get_network_info(active_interface)
            
        if info and info['ip']:
            # Détermine le type de connexion
            connection_type = "Ethernet" if any(eth_id in active_interface.lower() for eth_id in ['eth', 'en', 'eno', 'enp']) else "Wi-Fi"
            
            return {
                'interface': active_interface,
                'ip': info['ip'],
                'subnet_mask': info['subnet_mask'],
                'connection_type': connection_type
            }
        
        return None
    
    except Exception as e:
        print(f"Erreur lors de la récupération des informations sur l'interface : {e}")
        return None

# Exemple d'utilisation, exécuté uniquement si le fichier est lancé directement
if __name__ == "__main__":
    interface_info = get_interface_info()
    if interface_info:
        print("=== Informations sur l'interface réseau ===")
        print(f"Interface : {interface_info['interface']}")
        print(f"Type de connexion : {interface_info['connection_type']}")
        print(f"Adresse IP : {interface_info['ip']}")
        print(f"Masque de sous-réseau : {interface_info['subnet_mask']}")
    else:
        print("Impossible de récupérer les informations sur l'interface réseau")