import os
import subprocess

def list_network_interfaces():
    """
    Liste les interfaces réseau disponibles sur un système Linux.
    """
    try:
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
    except Exception as e:
        print(f"Erreur lors de la récupération des interfaces réseau : {e}")
        return []

def choose_network_interface(interfaces):
    """
    Permet à l'utilisateur de choisir une interface réseau.
    """
    print("\nInterfaces réseau disponibles :")
    for idx, iface in enumerate(interfaces, start=1):
        print(f"{idx}. {iface}")

    while True:
        try:
            choice = int(input("\nEntrez le numéro de l'interface réseau à utiliser : "))
            if 1 <= choice <= len(interfaces):
                return interfaces[choice - 1]
            else:
                print("Veuillez entrer un numéro valide.")
        except ValueError:
            print("Veuillez entrer un numéro valide.")

def main():
    # Étape 1 : Lister les interfaces réseau
    interfaces = list_network_interfaces()
    if not interfaces:
        print("Aucune interface réseau disponible.")
        return

    # Étape 2 : Choisir une interface réseau
    selected_interface = choose_network_interface(interfaces)
    print(f"\nVous avez choisi l'interface réseau : {selected_interface}")

if __name__== "__main__":
    main()


