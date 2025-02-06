import os
import subprocess

def list_network_interfaces():
    # Exécuter la commande ip link show pour obtenir les interfaces réseau
    result = subprocess.run(["ip", "link", "show"], capture_output=True, text=True)
    output = result.stdout

    # Extraire les noms des interfaces réseau
    interfaces = []
    for line in output.splitlines():
        if ": " in line:
            parts = line.split(": ")
            if len(parts) > 1:
                interface = parts[1].split("@")[0].strip()
                if interface not in ("lo"):  # Ignorer l'interface lo (loopback)
                    interfaces.append(interface)
    return interfaces