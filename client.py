import requests
import platform
import time
import subprocess
import os
from io import BytesIO
from PIL import ImageGrab
import psutil

SERVER_URL = "http://10.100.8.254:5000" # Adaptez si votre serveur est ailleurs

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
        response = requests.get(f"{SERVER_URL}/client/{client_id}/getcommand")
        if response.status_code == 200:
            data = response.json()
            if 'command' in data and data['command']:
                command_to_execute = data['command']
                print(f"Commande reçue du serveur: {command_to_execute}")
                stdout, stderr = execute_command(command_to_execute)
                
                # Préparation de la réponse avec la sortie de la commande
                result = {
                    'stdout': stdout,
                    'stderr': stderr,
                    'command': command_to_execute
                }
                
                # Envoi du résultat au serveur
                requests.post(f"{SERVER_URL}/client/{client_id}/commandresult", json=result)
                
                if stdout:
                    print("Sortie de la commande:")
                    print(stdout)
                if stderr:
                    print("Erreur de la commande:")
                    print(stderr)
    except Exception as e:
        print(f"Erreur lors de la vérification des commandes: {e}")

import psutil  # Assurez-vous d'installer psutil via pip

def collect_system_resources():
    try:
        cpu_usage = psutil.cpu_percent(interval=1)
        ram_total = round(psutil.virtual_memory().total / 1073741824)  # En GB
        ram_used = round(psutil.virtual_memory().used / 1073741824, 2)  # En GB
        ram_percent = psutil.virtual_memory().percent
        
        resources = {
            'cpu_usage': cpu_usage,
            'ram_total': ram_total,
            'ram_used': ram_used,
            'ram_percent': ram_percent,
            'cpu_threshold_exceeded': cpu_usage >= CPU_threshold,
            'ram_threshold_exceeded': ram_percent >= RAM_threshold
        }
        
        return resources
    except Exception as e:
        print(f"Erreur lors de la collecte des ressources système: {e}")
        return None

def main():
    client_name = get_computer_name()
    os_type = get_os_type()
    
    # Définir les seuils
    global CPU_threshold, RAM_threshold
    CPU_threshold = 95
    RAM_threshold = 80

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

    if client_id is None:
        print("ID client non obtenu, arrêt.")
        return

    while True:
        # Check-in régulier
        try:
            requests.post(f"{SERVER_URL}/client/checkin", json=checkin_data)
        except requests.exceptions.RequestException as e:
            print(f"Erreur lors du check-in régulier: {e}")

        # Capture d'écran et envoi au serveur
        screenshot_data = capture_screenshot()
        if screenshot_data:
            try:
                files = {'screenshot': ('screenshot.png', BytesIO(screenshot_data), 'image/png')}
                requests.post(f"{SERVER_URL}/client/{client_id}/screenshot", files=files)
            except requests.exceptions.RequestException as e:
                print(f"Erreur de connexion lors de l'envoi du screenshot: {e}")

        # Collecte et envoi des ressources système
        resources = collect_system_resources()
        if resources:
            try:
                requests.post(f"{SERVER_URL}/client/{client_id}/resources", json=resources)
            except requests.exceptions.RequestException as e:
                print(f"Erreur lors de l'envoi des ressources système: {e}")

        # Vérification des commandes
        check_for_command(client_id)

        time.sleep(0.1)  # Attendre 5 secondes avant la prochaine itération


if __name__ == "__main__":
    main()