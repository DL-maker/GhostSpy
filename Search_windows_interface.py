import subprocess
import re

def list_network_interfaces():
    # Commande PowerShell pour obtenir les interfaces réseau avec UTF-8 en sortie
        command = ["powershell", "-Command", "[Console]::OutputEncoding = [System.Text.Encoding]::UTF8; Get-NetAdapter"]
        result = subprocess.run(command, capture_output=True, text=False)  # Capture les bytes pour inspection

        # Affichage des bytes bruts pour débogage
        print(f"Bytes reçus :\n{result.stdout}\n")

        # Décodage explicite en UTF-8 pour les résultats de PowerShell
        output = result.stdout.decode('utf-8')
        print(f"Texte décodé en UTF-8 :\n{output}\n")

        # Expression régulière pour extraire les interfaces réseau actives
        interfaces = []
        matches = re.findall(r"^\s*(.*?)\s{2,}.*?Up", output, re.MULTILINE) # Recherche des interfaces actives

        # Filtrer les interfaces actives et les ajouter à la liste
        for interface in matches:
            # Nettoyer l'interface et l'ajouter à la liste
            interfaces.append(interface.strip())
        return interfaces