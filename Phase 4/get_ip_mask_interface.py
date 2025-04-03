import subprocess
import platform
import re
import psutil

def get_active_internet_interface():
    """
    Определяет активный интерфейс подключения к интернету
    Возвращает имя активного интерфейса или None, если активное подключение не найдено
    """
    try:
        # Проверяем все интерфейсы с помощью psutil
        net_if_addrs = psutil.net_if_addrs()
        net_if_stats = psutil.net_if_stats()
        
        # Сначала проверяем проводные подключения, потом беспроводные (приоритет Ethernet)
        ethernet_interfaces = []
        wifi_interfaces = []
        
        for interface, stats in net_if_stats.items():
            # Пропускаем выключенные интерфейсы и локальный loopback
            if not stats.isup or interface.lower() == 'lo' or 'loopback' in interface.lower():
                continue
                
            # Проверяем наличие IP-адреса (кроме localhost)
            has_valid_ip = False
            if interface in net_if_addrs:
                for addr in net_if_addrs[interface]:
                    # Проверяем только IPv4 адреса (AF_INET = 2 для IPv4)
                    if addr.family == 2 and addr.address != '127.0.0.1':
                        has_valid_ip = True
                        break
                        
            if not has_valid_ip:
                continue
                
            # Если интерфейс активен и имеет IP, добавляем его в соответствующий список
            if any(eth_id in interface.lower() for eth_id in ['eth', 'en', 'eno', 'enp']):
                ethernet_interfaces.append(interface)
            elif any(wifi_id in interface.lower() for wifi_id in ['wlan', 'wi-fi', 'wireless', 'wl', 'wifi']):
                wifi_interfaces.append(interface)
        
        # Возвращаем интерфейс согласно приоритету: сначала Ethernet, потом Wi-Fi
        if ethernet_interfaces:
            return ethernet_interfaces[0]
        elif wifi_interfaces:
            return wifi_interfaces[0]
            
        return None
    except Exception as e:
        print(f"Ошибка при определении активного интерфейса: {e}")
        return None

def get_network_info(interface):
    """Получает сетевую информацию указанного интерфейса"""
    try:
        if platform.system() == 'Windows':
            result = subprocess.check_output([
                'wmic', 'nicconfig', 'where', f'index={interface}',
                'get', 'IPAddress,IPSubnet'
            ]).decode(errors='ignore').strip()
            
            info = {
                'ip': None,
                'subnet_mask': None
            }
            
            for line in result.split('\n'):
                if '.' in line:
                    parts = line.split()
                    if len(parts) > 1:
                        info['ip'] = parts[0]
                        info['subnet_mask'] = parts[1]
                        break
        else:
            result = subprocess.check_output([
                'ip', 'addr', 'show', interface
            ]).decode(errors='ignore').strip()
            
            info = {
                'ip': None,
                'subnet_mask': '255.255.255.0'  # Стандартная маска по умолчанию
            }
            
            for line in result.split('\n'):
                if 'inet ' in line:
                    parts = line.split()
                    if len(parts) > 1:
                        # Извлекаем IP-адрес и префикс CIDR
                        ip_with_cidr = parts[1]
                        if '/' in ip_with_cidr:
                            info['ip'] = ip_with_cidr.split('/')[0]
                            # Преобразуем префикс CIDR в маску подсети
                            cidr = int(ip_with_cidr.split('/')[1])
                            info['subnet_mask'] = cidr_to_netmask(cidr)
                        else:
                            info['ip'] = ip_with_cidr
        
        return info
    except Exception as e:
        print(f"Ошибка при получении сетевой информации для {interface}: {e}")
        return None

def cidr_to_netmask(cidr):
    """Преобразует префикс CIDR в маску подсети"""
    binary = ('1' * cidr).ljust(32, '0')
    octets = [binary[i:i+8] for i in range(0, 32, 8)]
    return '.'.join(str(int(octet, 2)) for octet in octets)

def get_interface_info():
    """
    Возвращает словарь с информацией об активном сетевом интерфейсе:
    - имя интерфейса
    - IP-адрес
    - маска подсети
    - тип подключения (Wi-Fi или Ethernet)
    """
    try:
        # Получаем активный интерфейс
        active_interface = get_active_internet_interface()
        
        if not active_interface:
            return None
            
        # Получаем информацию об интерфейсе
        info = None
        
        # Для Windows используем индекс интерфейса
        if platform.system() == 'Windows':
            # Преобразуем имя интерфейса в индекс для Windows
            interfaces_output = subprocess.check_output(['wmic', 'nic', 'get', 'Name,Index']).decode(errors='ignore').strip()
            for line in interfaces_output.split('\n'):
                if active_interface in line:
                    parts = line.split()
                    if parts:
                        index = parts[0]
                        info = get_network_info(index)
                        if info and info['ip']:
                            break
        else:
            # Для Linux используем имя интерфейса напрямую
            info = get_network_info(active_interface)
            
        if info and info['ip']:
            # Определяем тип подключения
            connection_type = "Ethernet" if any(eth_id in active_interface.lower() for eth_id in ['eth', 'en', 'eno', 'enp']) else "Wi-Fi"
            
            return {
                'interface': active_interface,
                'ip': info['ip'],
                'subnet_mask': info['subnet_mask'],
                'connection_type': connection_type
            }
        
        return None
    
    except Exception as e:
        print(f"Ошибка при получении информации об интерфейсе: {e}")
        return None

# Пример использования, выполняется только при прямом запуске файла
if __name__ == "__main__":
    interface_info = get_interface_info()
    if interface_info:
        print("=== Информация о сетевом интерфейсе ===")
        print(f"Интерфейс: {interface_info['interface']}")
        print(f"Тип подключения: {interface_info['connection_type']}")
        print(f"IP-адрес: {interface_info['ip']}")
        print(f"Маска подсети: {interface_info['subnet_mask']}")
    else:
        print("Не удалось получить информацию о сетевом интерфейсе")