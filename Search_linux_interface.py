import os
import subprocess

def list_network_interfaces():
    # Execute la commande ip link show pour obtenir les interphaces réseau
    result = subprocess.run(["ip", "link", "show"], capture_output=True, text=True)
    output = result.stdout
    # Extraire les nom des interphaces réseau
    interfaces = []
    for line in output.splitlines():
        if ": " in line:
            parts = line.split(": ")
            if len(parts) > 1: #Si il y a plus qu'un interphace 
                interface = parts[1].split("@")[0].strip()
                if interface not in ("lo"):  # Ignoree l'interphace lo
                    interfaces.append(interface)
    return interfaces