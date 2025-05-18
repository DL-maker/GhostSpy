import platform
import subprocess
import re
import os
import json
import socket

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
        output = subprocess.check_output(['route', 'print'], shell=True).decode('utf-8', errors='ignore')
    except subprocess.CalledProcessError:
        return []
    
    start = output.find("IPv4 Route Table")
    if start == -1:
        return []
    
    end = output.find("=", start)
    table = output[start:end].splitlines()
    
    routes = []
    for line in table:
        # Extract the default gateway, interface IP, and metric from the route table
        if "0.0.0.0" in line and not line.strip().startswith("Network Destination"):
            parts = re.split(r'\s+', line.strip())
            if len(parts) >= 5:
                gateway = parts[2]
                interface_ip = parts[3]
                metric = int(parts[4]) if parts[4].isdigit() else 9999
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
        output = subprocess.check_output(['ipconfig', '/all'], shell=True).decode('utf-8', errors='ignore')
    except subprocess.CalledProcessError:
        return {}
    
    sections = re.split(r'\r\n\r\n', output)
    adapters = {}
    current_adapter = None
    adapter_data = {}
    
    # Process each section of the output to extract network adapter details
    for section in sections:
        lines = section.split('\r\n')
        if not lines:
            continue
            
        if lines[0] and not lines[0].startswith(' '):
            # This is an adapter name line
            if current_adapter and 'IPv4 Address' in adapter_data:
                ip = adapter_data['IPv4 Address'].split('(')[0].strip()
                adapters[ip] = adapter_data
            
            current_adapter = lines[0]
            adapter_data = {}
            
        for line in lines[1:]:
            if ':' in line:
                key, value = line.split(':', 1)
                key = key.strip()
                value = value.strip()
                adapter_data[key] = value
    
    # Add the last adapter if it has an IPv4 address
    if current_adapter and 'IPv4 Address' in adapter_data:
        ip = adapter_data['IPv4 Address'].split('(')[0].strip()
        adapters[ip] = adapter_data
    
    return adapters

def get_windows_subnet_mask(adapters, interface_ip):
    # Get the subnet mask for a given interface on Windows
    if interface_ip in adapters:
        return adapters[interface_ip].get('Subnet Mask', None)
    return None

def get_windows_dhcp_server(adapters, interface_ip):
    # Get the DHCP server IP address for a given interface on Windows
    if interface_ip in adapters:
        return adapters[interface_ip].get('DHCP Server', None)
    return None

def get_windows_dns_server(adapters, interface_ip):
    # Get the DNS server IP address for a given interface on Windows
    if interface_ip in adapters:
        dns_servers = adapters[interface_ip].get('DNS Servers', None)
        if dns_servers:
            return dns_servers.split()[0] if ' ' in dns_servers else dns_servers
    return None

def get_windows_default_gateways(routes):
    # Return the list of default gateways from the Windows route table
    return [r['gateway'] for r in routes if r['gateway'] != '0.0.0.0']

# Alternative Windows methods using WMI when standard methods fail
def get_windows_network_info_wmi():
    try:
        import wmi
        c = wmi.WMI()
        
        # Get network configuration
        nic_configs = c.Win32_NetworkAdapterConfiguration(IPEnabled=True)
        
        if not nic_configs:
            return None, None, None, None
            
        # Find the active adapter (the one with a default gateway)
        active_nic = None
        for nic in nic_configs:
            if nic.DefaultIPGateway:
                active_nic = nic
                break
        
        if not active_nic:
            active_nic = nic_configs[0]  # Take the first one if none have a gateway
            
        dhcp_server = active_nic.DHCPServer if hasattr(active_nic, 'DHCPServer') else None
        dns_servers = active_nic.DNSServerSearchOrder[0] if hasattr(active_nic, 'DNSServerSearchOrder') and active_nic.DNSServerSearchOrder else None
        default_gateway = active_nic.DefaultIPGateway[0] if hasattr(active_nic, 'DefaultIPGateway') and active_nic.DefaultIPGateway else None
        subnet_mask = active_nic.IPSubnet[0] if hasattr(active_nic, 'IPSubnet') and active_nic.IPSubnet else None
        
        return dhcp_server, dns_servers, default_gateway, subnet_mask
    except:
        return None, None, None, None

# Main function to retrieve network configuration based on the OS
def get_network_configuration():
    system = platform.system()
    
    # Handle Linux system
    if system == 'Linux':
        routes = get_linux_default_routes()
        if not routes:
            return {
                "dhcp_server_ip": "Non disponible",
                "dns_server_ip": "Non disponible",
                "default_gateway(s)": "Non disponible",
                "subnet_mask": "Non disponible"
            }
        primary_interface = get_linux_primary_interface(routes)
        subnet_mask = get_linux_subnet_mask(primary_interface)
        dhcp_server_ip = get_linux_dhcp_server(primary_interface)
        dns_server_ip = get_linux_dns_server()
        default_gateways = get_linux_default_gateways(routes)
    
    # Handle Windows system
    elif system == 'Windows':
        # Try the standard approach first
        routes = get_windows_default_routes()
        default_gateways = "Non disponible"
        subnet_mask = "Non disponible"
        dhcp_server_ip = "Non disponible"
        dns_server_ip = "Non disponible"
        
        if routes:
            primary_interface_ip = get_windows_primary_interface_ip(routes)
            adapters = parse_ipconfig()
            
            if primary_interface_ip and adapters:
                subnet_mask = get_windows_subnet_mask(adapters, primary_interface_ip)
                dhcp_server_ip = get_windows_dhcp_server(adapters, primary_interface_ip)
                dns_server_ip = get_windows_dns_server(adapters, primary_interface_ip) 
                default_gateways = get_windows_default_gateways(routes)
            
        # If the standard approach failed, try the WMI approach
        if dhcp_server_ip == "Non disponible" and dns_server_ip == "Non disponible":
            try:
                dhcp, dns, gateway, subnet = get_windows_network_info_wmi()
                if dhcp:
                    dhcp_server_ip = dhcp
                if dns:
                    dns_server_ip = dns
                if gateway:
                    default_gateways = gateway
                if subnet:
                    subnet_mask = subnet
            except:
                pass
                
        # Last resort - try to get DNS servers directly
        if dns_server_ip == "Non disponible":
            try:
                output = subprocess.check_output(['nslookup'], shell=True, stderr=subprocess.STDOUT, timeout=3).decode('utf-8', errors='ignore')
                match = re.search(r'Server:\s+(\d+\.\d+\.\d+\.\d+)', output)
                if match:
                    dns_server_ip = match.group(1)
            except:
                pass
    
    # Return None if system is unsupported
    else:
        return {
            "dhcp_server_ip": "Non disponible",
            "dns_server_ip": "Non disponible",
            "default_gateway(s)": "Non disponible",
            "subnet_mask": "Non disponible"
        }

    # Return the network configuration as a dictionary
    return {
        "dhcp_server_ip": dhcp_server_ip or "Non disponible",
        "dns_server_ip": dns_server_ip or "Non disponible",
        "default_gateway(s)": default_gateways or "Non disponible",
        "subnet_mask": subnet_mask or "Non disponible"
    }

# Using the script to get the network configuration
config = get_network_configuration()