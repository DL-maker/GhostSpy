import platform
import subprocess
import re
import os
import json

# Functions for Linux

def get_linux_default_routes():
    # Get default routing information on a Linux system
    try:
        output = subprocess.check_output(['ip', 'route', 'show', 'default']).decode()
    except subprocess.CalledProcessError:
        return []
    
    routes = []
    # Parse the output of the 'ip route' command to extract gateway and interface information
    for line in output.splitlines():
        match = re.search(r'default via (\S+) dev (\S+)( metric (\d+))?', line)
        if match:
            gateway = match.group(1)
            interface = match.group(2)
            metric = int(match.group(4)) if match.group(4) else 0
            routes.append({'gateway': gateway, 'interface': interface, 'metric': metric})
    
    return routes

def get_linux_primary_interface(routes):
    # Get the primary network interface (the one with the lowest metric)
    if not routes:
        return None
    primary = min(routes, key=lambda x: x['metric'])
    return primary['interface']

def get_linux_subnet_mask(interface):
    # Get the subnet mask for the specified network interface on Linux
    try:
        output = subprocess.check_output(['ip', 'addr', 'show', 'dev', interface]).decode()
    except subprocess.CalledProcessError:
        return None
    
    # Parse the output to extract subnet mask in dotted decimal format
    for line in output.splitlines():
        if 'inet ' in line and 'brd' in line:
            match = re.search(r'inet \S+/\d+', line)
            if match:
                cidr = match.group(0).split('/')[1]
                prefix = int(cidr)
                mask = (0xffffffff << (32 - prefix)) & 0xffffffff
                return '.'.join(str((mask >> 8 * i) & 0xff) for i in range(3, -1, -1))
    
    return None

def get_linux_dhcp_server(interface):
    # Get the DHCP server IP address by parsing the DHCP lease files
    lease_files = ['/var/lib/dhcp/dhclient.leases', '/var/lib/dhclient/dhclient.leases']
    for lease_file in lease_files:
        if os.path.exists(lease_file):
            with open(lease_file, 'r') as f:
                content = f.read()
            # Search for the DHCP server identifier in the lease file
            pattern = re.compile(r'lease\s*{\s*interface\s+"{}";.*?dhcp-server-identifier\s+(\S+);'.format(interface), re.DOTALL | re.IGNORECASE)
            match = pattern.search(content)
            if match:
                return match.group(1)
    return None

def get_linux_dns_server():
    # Get the DNS server IP by reading the /etc/resolv.conf file on Linux
    if os.path.exists('/etc/resolv.conf'):
        with open('/etc/resolv.conf', 'r') as f:
            for line in f:
                if line.startswith('nameserver'):
                    return line.split()[1]
    return None

def get_linux_default_gateways(routes):
    # Return the list of default gateways from the routes
    return [r['gateway'] for r in routes]

# Functions for Windows

def get_windows_default_routes():
    # Get default routing information on a Windows system using the 'route print' command
    try:
        output = subprocess.check_output(['route', 'print']).decode('utf-8', errors='ignore')
    except subprocess.CalledProcessError:
        return []
    
    start = output.find("IPv4 Route Table")
    if start == -1:
        return []
    
    end = output.find("=\r\n", start)
    table = output[start:end].splitlines()
    
    routes = []
    for line in table:
        # Extract the default gateway, interface IP, and metric from the route table
        if line.strip().startswith("  0.0.0.0        0.0.0.0"):
            parts = line.split()
            if len(parts) >= 5:
                gateway = parts[2]
                interface_ip = parts[3]
                metric = int(parts[4])
                routes.append({'gateway': gateway, 'interface_ip': interface_ip, 'metric': metric})
    
    return routes

def get_windows_primary_interface_ip(routes):
    # Get the IP address of the primary network interface (lowest metric) on Windows
    if not routes:
        return None
    primary = min(routes, key=lambda x: x['metric'])
    return primary['interface_ip']

def parse_ipconfig():
    # Parse the output of 'ipconfig /all' to get detailed information about network interfaces
    try:
        output = subprocess.check_output(['ipconfig', '/all']).decode('utf-8', errors='ignore')
    except subprocess.CalledProcessError:
        return {}
    
    sections = output.split('\r\n\r\n')
    adapters = {}
    
    # Process each section of the output to extract network adapter details
    for section in sections:
        lines = section.split('\r\n')
        if lines and not lines[0].startswith('Windows IP Configuration'):
            config = {}
            for line in lines:
                if ':' in line:
                    key, value = line.split(':', 1)
                    config[key.strip()] = value.strip()
            for k, v in list(config.items()):
                if 'IPv4 Address' in k:
                    ip = v
                    adapters[ip] = config
                    break
    
    return adapters

def get_windows_subnet_mask(adapters, interface_ip):
    # Get the subnet mask for a given interface on Windows
    if interface_ip in adapters:
        for k, v in adapters[interface_ip].items():
            if 'Subnet Mask' in k:
                return v
    return None

def get_windows_dhcp_server(adapters, interface_ip):
    # Get the DHCP server IP address for a given interface on Windows
    if interface_ip in adapters:
        for k, v in adapters[interface_ip].items():
            if 'DHCP Server' in k:
                return v
    return None

def get_windows_dns_server(adapters, interface_ip):
    # Get the DNS server IP address for a given interface on Windows
    if interface_ip in adapters:
        for k, v in adapters[interface_ip].items():
            if 'DNS Servers' in k:
                dns_servers = v.split()
                return dns_servers[0] if dns_servers else None
    return None

def get_windows_default_gateways(routes):
    # Return the list of default gateways from the Windows route table
    return [r['gateway'] for r in routes]

# Main function to retrieve network configuration based on the OS
def get_network_configuration():
    system = platform.system()
    
    # Handle Linux system
    if system == 'Linux':
        routes = get_linux_default_routes()
        if not routes:
            return None
        primary_interface = get_linux_primary_interface(routes)
        subnet_mask = get_linux_subnet_mask(primary_interface)
        dhcp_server_ip = get_linux_dhcp_server(primary_interface)
        dns_server_ip = get_linux_dns_server()
        default_gateways = get_linux_default_gateways(routes)
    
    # Handle Windows system
    elif system == 'Windows':
        routes = get_windows_default_routes()
        if not routes:
            return None
        primary_interface_ip = get_windows_primary_interface_ip(routes)
        adapters = parse_ipconfig()
        subnet_mask = get_windows_subnet_mask(adapters, primary_interface_ip)
        dhcp_server_ip = get_windows_dhcp_server(adapters, primary_interface_ip)
        dns_server_ip = get_windows_dns_server(adapters, primary_interface_ip)
        default_gateways = get_windows_default_gateways(routes)
    
    # Return None if system is unsupported
    else:
        return None

    # Return the network configuration as a dictionary
    return {
        "dhcp_server_ip": dhcp_server_ip,
        "dns_server_ip": dns_server_ip,
        "default_gateway(s)": default_gateways,
        "subnet_mask": subnet_mask
    }

# Using the script to get the network configuration
config = get_network_configuration()
