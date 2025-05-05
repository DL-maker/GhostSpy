import requests
import platform
import time
import subprocess
import os
from io import BytesIO
from PIL import ImageGrab
import psutil
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import datetime
import hashlib
import json
import threading
import logging
import colorama  # Add colorama for colored console output

# Initialize colorama
colorama.init(autoreset=True)

# Configuration
SERVER_URL = "http://127.0.0.1:5000"  # Adaptez si votre serveur est ailleurs
API_KEY = "API"  # Remplacez par votre clé API VirusTotal
VT_BASE_URL = "https://www.virustotal.com/api/v3"
LOG_FILE = "client_vt.log"

# Dossier Downloads
DOWNLOADS_FOLDER = os.path.join(os.path.expanduser("~"), "Downloads")

# Seuil de temps pour considérer qu'un fichier est récent (en minutes)
RECENT_THRESHOLD_MINUTES = 5

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE, encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('ClientVT')

# Ajout des extensions .jpg et .jpeg pour scanner les images téléchargées
MONITORED_EXTENSIONS = [
    '.exe', '.dll', '.bat', '.cmd', '.ps1', '.vbs', '.msi', '.scr', 
    '.zip', '.rar', '.7z', '.pdf', '.doc', '.docx', '.xls', '.xlsx', 
    '.js', '.jar', '.jpg', '.jpeg'
]
# Monitorer tous les dossiers utilisateur pour les logs mais uniquement Downloads pour VirusTotal
MONITORED_FOLDERS = ['Downloads', 'Desktop', 'Documents', 'Pictures', 'Videos', 'Music']
VT_SCAN_FOLDERS = ['Downloads']

class ClientLogs:
    def __init__(self):
        self.logs = []
        self.lock = threading.Lock()

    def add_log(self, level, message):
        with self.lock:
            log_entry = {
                'timestamp': datetime.datetime.now().isoformat(),
                'level': level,
                'message': message
            }
            self.logs.append(log_entry)
            if len(self.logs) > 100:
                self.logs = self.logs[-100:]

    def get_logs(self):
        with self.lock:
            return list(self.logs)

    def clear(self):
        with self.lock:
            self.logs = []

client_logs = ClientLogs()

def send_client_logs(client_id):
    while True:
        try:
            # Add system info to logs
            client_logs.add_log(
                "INFO",
                f"État système: CPU {psutil.cpu_percent()}%, RAM {psutil.virtual_memory().percent}%"
            )
            
            logs = client_logs.get_logs()
            if logs:
                # Send logs to server
                response = requests.post(f"{SERVER_URL}/client/{client_id}/logs", json=logs, timeout=10)
                
                if response.status_code == 200:
                    print(colorama.Fore.GREEN + "✅ Logs envoyés au serveur")
                    client_logs.clear()
                else:
                    print(colorama.Fore.YELLOW + f"⚠️ Erreur lors de l'envoi des logs: {response.status_code}")
                    logger.warning(f"Erreur lors de l'envoi des logs: {response.status_code}")
        except Exception as e:
            print(colorama.Fore.RED + f"❌ Erreur lors de l'envoi des logs: {str(e)}")
            logger.error(f"Erreur inattendue lors de l'envoi des logs: {e}")
            
        time.sleep(20)  # Send logs every 20 seconds

def get_os_type():
    return platform.system()

def get_computer_name():
    return platform.node()

def capture_screenshot():
    try:
        screenshot = ImageGrab.grab()
        img_byte_arr = BytesIO()
        screenshot.save(img_byte_arr, format='PNG')
        return img_byte_arr.getvalue()
    except Exception as e:
        logger.error(f"Erreur lors de la capture d'écran: {e}")
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
                logger.info(f"Commande reçue du serveur: {command_to_execute}")
                stdout, stderr = execute_command(command_to_execute)
                result = {'stdout': stdout, 'stderr': stderr, 'command': command_to_execute}
                requests.post(f"{SERVER_URL}/client/{client_id}/commandresult", json=result)
    except Exception as e:
        logger.error(f"Erreur lors de la vérification des commandes: {e}")
def change_api(api):
    global API_KEY
    API_KEY = api
    print("Clé API mise à jour:", API_KEY)
    return API_KEY

    
def check_for_api(client_id):
    try:
        response = requests.get(f"{SERVER_URL}/client/{client_id}/token")
      
        if response.status_code == 200:

            data = response.json()
            print(data)
            if 'api' in data and data['api']:
                api_to_execute = data['api']
                logger.info(f"Api reçue du serveur: {api_to_execute}")
                key = change_api(api_to_execute)
                result = {'stdout': stdout, 'stderr': stderr, 'command': api_to_execute}
                requests.post(f"{SERVER_URL}/client/{client_id}/commandresult", json=result)
    except Exception as e:
        logger.error(f"Erreur lors de la vérification API: {e}")

def collect_system_resources():
    try:
        cpu_usage = psutil.cpu_percent(interval=1)
        ram_total = round(psutil.virtual_memory().total / 1073741824)
        ram_used = round(psutil.virtual_memory().used / 1073741824, 2)
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
        logger.error(f"Erreur lors de la collecte des ressources système: {e}")
        return None

def upload_file_to_vt(file_path):
    try:
        file_name = os.path.basename(file_path)
        url = f"{VT_BASE_URL}/files"
        headers = {"x-apikey": API_KEY}
        logger.info(f"Téléchargement de {file_name} vers VirusTotal...")
        with open(file_path, "rb") as f:
            files = {"file": (file_name, f)}
            response = requests.post(url, headers=headers, files=files, timeout=60)
        if response.status_code == 200:
            data = response.json()
            analysis_id = data.get("data", {}).get("id")
            logger.info(f"Fichier {file_name} téléchargé avec succès. ID d'analyse: {analysis_id}")
            return analysis_id
        else:
            logger.error(f"Échec téléchargement pour {file_name}: {response.status_code} {response.text}")
    except Exception as e:
        logger.error(f"Erreur lors du téléchargement de {os.path.basename(file_path)}: {e}")
    return None

def get_analysis_report(analysis_id):
    try:
        url = f"{VT_BASE_URL}/analyses/{analysis_id}"
        headers = {"x-apikey": API_KEY}
        logger.info(f"Récupération du rapport pour l'analyse {analysis_id}...")
        response = requests.get(url, headers=headers, timeout=60)
        if response.status_code == 200:
            return response.json()
        logger.error(f"Échec récupération rapport: {response.status_code} {response.text}")
    except Exception as e:
        logger.error(f"Erreur récupération rapport pour {analysis_id}: {e}")
    return None

def analyze_file_with_vt(file_path, client_id):
    try:
        file_name = os.path.basename(file_path)
        logger.info(f"Analyse du fichier: {file_name}")
        scan_result = {
            "file_name": file_name,
            "file_path": file_path,
            "scan_date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "status": "error",
            "error_message": None
        }
        file_size = os.path.getsize(file_path)
        if file_size > 32 * 1024 * 1024:
            scan_result["error_message"] = "Fichier trop volumineux (>32MB)"
            logger.warning(f"Fichier trop volumineux pour analyse: {file_name} ({file_size} bytes)")
            send_scan_result_to_server(scan_result, client_id)
            return

        file_hash = calculate_file_hash(file_path)
        scan_result["file_hash"] = file_hash

        try:
            report_url = f"{VT_BASE_URL}/files/{file_hash}"
            headers = {"x-apikey": API_KEY}
            response = requests.get(report_url, headers=headers)
            if response.status_code == 429:
                scan_result["error_message"] = "Quota VirusTotal dépassé - Analyse locale uniquement"
                scan_result["status"] = "quota_exceeded"
                scan_result["local_check"] = perform_local_check(file_path)
                send_scan_result_to_server(scan_result, client_id)
                logger.error(f"Quota VirusTotal dépassé pour {file_name}")
                return
            if response.status_code == 200:
                result_data = response.json()
                scan_result["status"] = "complete"
                scan_result["result"] = extract_vt_results(result_data)
                send_scan_result_to_server(scan_result, client_id)
                logger.info(f"Résultat d'analyse trouvé pour {file_name}")
                return
        except Exception as e:
            logger.error(f"Erreur lors de la vérification du rapport: {e}")

        try:
            upload_url = f"{VT_BASE_URL}/files"
            files = {"file": (file_name, open(file_path, "rb"))}
            headers = {"x-apikey": API_KEY}
            response = requests.post(upload_url, files=files, headers=headers)
            if response.status_code == 429:
                scan_result["error_message"] = "Quota VirusTotal dépassé lors du téléchargement - Analyse locale uniquement"
                scan_result["status"] = "quota_exceeded"
                scan_result["local_check"] = perform_local_check(file_path)
                send_scan_result_to_server(scan_result, client_id)
                logger.error(f"Échec téléchargement pour {file_name}: {response.status_code} {response.text}")
                return
            if response.status_code == 200:
                result = response.json()
                analysis_id = result.get("data", {}).get("id")
                if analysis_id:
                    scan_result["analysis_id"] = analysis_id
                    scan_result["status"] = "pending"
                    send_scan_result_to_server(scan_result, client_id)
                    time.sleep(10)
                    get_analysis_result(analysis_id, client_id, file_name)
                else:
                    scan_result["error_message"] = "Impossible d'obtenir un ID d'analyse"
                    send_scan_result_to_server(scan_result, client_id)
            else:
                scan_result["error_message"] = f"Échec du téléchargement: {response.status_code}"
                send_scan_result_to_server(scan_result, client_id)
                logger.error(f"Échec téléchargement pour {file_name}: {response.status_code} {response.text}")
        except Exception as e:
            scan_result["error_message"] = str(e)
            send_scan_result_to_server(scan_result, client_id)
            logger.error(f"Erreur lors de l'analyse du fichier {file_name}: {e}")
    except Exception as e:
        logger.error(f"Erreur critique lors de l'analyse: {e}")

def calculate_file_hash(file_path):
    try:
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except Exception as e:
        logger.error(f"Erreur lors du calcul du hash pour {file_path}: {e}")
        return None

def send_scan_result_to_server(scan_result, client_id):
    try:
        response = requests.post(f"{SERVER_URL}/client/{client_id}/scan_file", json=scan_result)
        if response.status_code == 200:
            logger.info(f"Résultats d'analyse pour {scan_result['file_name']} envoyés avec succès")
        else:
            logger.error(f"Erreur lors de l'envoi des résultats: {response.text}")
    except Exception as e:
        logger.error(f"Erreur lors de l'envoi des résultats au serveur: {e}")

def extract_vt_results(result_data):
    try:
        stats = result_data.get("data", {}).get("attributes", {}).get("stats", {})
        malicious = stats.get('malicious', 0)
        suspicious = stats.get('suspicious', 0)
        total_detections = malicious + suspicious
        total_engines = stats.get('total', 0)
        is_malicious = total_detections > 0
        result = {
            'malicious': malicious,
            'suspicious': suspicious,
            'total_engines': total_engines,
            'is_malicious': is_malicious,
            'summary': f"{total_detections} détections sur {total_engines} moteurs"
        }
        if is_malicious:
            detected_engines = {}
            for engine, res in result_data.get("data", {}).get("attributes", {}).get("results", {}).items():
                if res.get('category') in ['malicious', 'suspicious']:
                    detected_engines[engine] = {
                        'result': res.get('result'),
                        'category': res.get('category')
                    }
            result['detected_engines'] = detected_engines
        return result
    except Exception as e:
        logger.error(f"Erreur lors de l'extraction des résultats VirusTotal: {e}")
        return {"error": str(e)}

def get_analysis_result(analysis_id, client_id, file_name):
    try:
        url = f"{VT_BASE_URL}/analyses/{analysis_id}"
        headers = {"x-apikey": API_KEY}
        response = requests.get(url, headers=headers)
        if response.status_code == 429:
            logger.error(f"Quota dépassé lors de la récupération du résultat pour {file_name}")
            scan_result = {
                "file_name": file_name,
                "analysis_id": analysis_id,
                "scan_date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "status": "quota_exceeded",
                "error_message": "Quota dépassé lors de la récupération des résultats"
            }
            send_scan_result_to_server(scan_result, client_id)
            return
        if response.status_code == 200:
            data = response.json()
            status = data.get("data", {}).get("attributes", {}).get("status")
            if status == "completed":
                result = extract_vt_results(data)
                scan_result = {
                    "file_name": file_name,
                    "analysis_id": analysis_id,
                    "scan_date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "status": "complete",
                    "result": result
                }
                send_scan_result_to_server(scan_result, client_id)
                logger.info(f"Analyse terminée pour {file_name}")
            else:
                logger.info(f"Analyse en cours pour {file_name}, status: {status}")
                time.sleep(10)
                get_analysis_result(analysis_id, client_id, file_name)
        else:
            logger.error(f"Erreur lors de la récupération du résultat: {response.status_code}")
            scan_result = {
                "file_name": file_name,
                "analysis_id": analysis_id,
                "scan_date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "status": "error",
                "error_message": f"Erreur API: {response.status_code}"
            }
            send_scan_result_to_server(scan_result, client_id)
    except Exception as e:
        logger.error(f"Erreur lors de la récupération du résultat pour {file_name}: {e}")

def perform_local_check(file_path):
    result = {
        "suspicious": False,
        "reasons": []
    }
    try:
        file_ext = os.path.splitext(file_path)[1].lower()
        suspicious_extensions = [".exe", ".bat", ".vbs", ".js", ".ps1", ".cmd"]
        if file_ext in suspicious_extensions:
            result["suspicious"] = True
            result["reasons"].append(f"Extension potentiellement dangereuse: {file_ext}")
        file_size = os.path.getsize(file_path)
        if file_size < 1000 and file_ext in suspicious_extensions:
            result["suspicious"] = True
            result["reasons"].append("Fichier exécutable de très petite taille (suspect)")
        with open(file_path, "rb") as f:
            header = f.read(8)
            if header.startswith(b"MZ"):
                result["file_type"] = "Exécutable Windows"
            if file_ext in [".js", ".vbs", ".ps1"]:
                with open(file_path, "r", errors="ignore") as script_file:
                    content = script_file.read(2000)
                    suspicious_patterns = ["eval(", "String.fromCharCode", "powershell -e", "hidden", "bypass"]
                    for pattern in suspicious_patterns:
                        if pattern in content.lower():
                            result["suspicious"] = True
                            result["reasons"].append(f"Pattern suspect détecté: {pattern}")
    except Exception as e:
        logger.error(f"Erreur lors de l'analyse locale: {e}")
        result["error"] = str(e)
    return result

class EventHandler(FileSystemEventHandler):
    def __init__(self, log_queue, client_id):
        self.log_queue = log_queue
        self.max_logs = 100
        self.client_id = client_id
        self.suspicious_extensions = MONITORED_EXTENSIONS
        self.scanned_files = set()

    def on_created(self, event):
        self.handle_event("created", event.src_path)

    def on_modified(self, event):
        self.handle_event("modified", event.src_path)

    def on_deleted(self, event):
        self.handle_event("deleted", event.src_path)

    def on_moved(self, event):
        self.handle_event("moved", event.src_path, dest_path=event.dest_path)

    def handle_event(self, event_type, src_path, dest_path=None):
        current_time = datetime.datetime.now().strftime("%H:%M:%S")
        is_directory = os.path.isdir(src_path) if os.path.exists(src_path) else False
        element_type = "folder" if is_directory else "file"
        if element_type == "file" and os.path.exists(src_path):
            file_ext = os.path.splitext(src_path)[1].lower()
            if file_ext in self.suspicious_extensions:
                element_type = "exe"
        name = os.path.basename(src_path)
        log_entry = {
            "time": current_time,
            "type": event_type,
            "element_type": element_type,
            "process_type": "user" if "Users" in src_path else "system",
            "name": name,
            "path": src_path
        }
        if event_type == "created" and element_type == "exe":
            log_entry["warning"] = "Fichier exécutable créé - peut présenter un risque de sécurité"
        elif event_type == "modified" and element_type == "exe":
            log_entry["warning"] = "Exécutable modifié - vérifiez l'authenticité de cette modification"
        if event_type == "moved" and dest_path:
            log_entry["dest_path"] = dest_path
        self.log_queue.append(log_entry)
        if len(self.log_queue) > self.max_logs:
            self.log_queue.pop(0)
        logger.info(f"[{current_time}] {event_type} de {'dossier' if is_directory else 'fichier'}: {name}")

        # Only scan files in Downloads folder with VirusTotal
        if (event_type in ["created", "modified"]) and not is_directory and os.path.exists(src_path):
            file_ext = os.path.splitext(src_path)[1].lower()
            file_mod_time = os.path.getmtime(src_path)
            time_threshold = time.time() - (RECENT_THRESHOLD_MINUTES * 60)
            
            # Check if the file is in Downloads folder
            is_in_downloads = DOWNLOADS_FOLDER in src_path
            
            if file_mod_time >= time_threshold and file_ext in MONITORED_EXTENSIONS and is_in_downloads:
                analyze_file_with_vt(src_path, self.client_id)

def scan_recent_files(client_id, minutes=RECENT_THRESHOLD_MINUTES, max_files=5):
    logger.info(f"Analyse des fichiers récents (dernières {minutes} minutes, maximum {max_files} fichiers)...")
    time_threshold = time.time() - (minutes * 60)
    potential_files = []
    try:
        # Only scan Downloads folder with VirusTotal
        user_folder = DOWNLOADS_FOLDER
        if os.path.exists(user_folder):
            for root, _, files in os.walk(user_folder):
                for file_name in files:
                    file_path = os.path.join(root, file_name)
                    if not os.path.isfile(file_path):
                        continue
                    file_mod_time = os.path.getmtime(file_path)
                    if file_mod_time < time_threshold:
                        continue
                    file_ext = os.path.splitext(file_path)[1].lower()
                    if file_ext not in MONITORED_EXTENSIONS:
                        continue
                    potential_files.append({
                        'path': file_path,
                        'name': file_name,
                        'ext': file_ext,
                        'mod_time': file_mod_time,
                        'size': os.path.getsize(file_path)
                    })
    except Exception as e:
        logger.error(f"Erreur lors du scan des dossiers surveillés: {e}")
    potential_files = sorted(potential_files, key=lambda x: x['mod_time'], reverse=True)[:max_files]
    for i, file_info in enumerate(potential_files):
        logger.info(f"Analyse {i+1}/{len(potential_files)}: {file_info['name']}")
        analyze_file_with_vt(file_info['path'], client_id)
        time.sleep(2)
    logger.info(f"Analyse terminée. {len(potential_files)} fichiers scannés.")
    return {"scanned": len(potential_files)}

def main():
    client_name = get_computer_name()
    os_type = get_os_type()

    global CPU_threshold, RAM_threshold
    CPU_threshold = 95
    RAM_threshold = 80

    checkin_data = {'name': client_name, 'os_type': os_type}
    try:
        response = requests.post(f"{SERVER_URL}/client/checkin", json=checkin_data)
        if response.status_code == 200:
            client_id_data = response.json()
            client_id = client_id_data.get('client_id')
            logger.info(f"Client enregistré avec l'ID: {client_id}")
        else:
            logger.error(f"Erreur lors du check-in initial: {response.status_code}")
            return
    except requests.exceptions.RequestException as e:
        logger.error(f"Erreur de connexion au serveur lors du check-in: {e}")
        return

    if client_id is None:
        logger.error("ID client non obtenu, arrêt.")
        return

    log_queue = []
    event_handler = EventHandler(log_queue, client_id)
    observer = Observer()

    # Modification: Configure monitoring for all folders in MONITORED_FOLDERS
    for folder_name in MONITORED_FOLDERS:
        user_folder = os.path.join(os.path.expanduser("~"), folder_name)
        if os.path.exists(user_folder):
            observer.schedule(event_handler, path=user_folder, recursive=True)
            logger.info(f"Surveillance du dossier {folder_name}: {user_folder}")
        else:
            logger.warning(f"Le dossier {folder_name} est introuvable.")

    observer.start()
    logger.info("Surveillance des fichiers démarrée")

    try:
        logger.info("Analyse des fichiers existants dans les dossiers surveillés...")
        for folder_name in MONITORED_FOLDERS:
            user_folder = os.path.join(os.path.expanduser("~"), folder_name)
            if os.path.exists(user_folder):
                for file_name in os.listdir(user_folder):
                    file_path = os.path.join(user_folder, file_name)
                    if os.path.isfile(file_path) and os.path.splitext(file_path)[1].lower() in MONITORED_EXTENSIONS:
                        if os.path.getmtime(file_path) >= time.time() - (RECENT_THRESHOLD_MINUTES * 60):
                            logger.info(f"Analyse du fichier existant dans {folder_name}: {file_name}")
                            event_handler.scan_file(file_path)
    except Exception as e:
        logger.error(f"Erreur lors de l'analyse des fichiers existants: {e}")

    # Start the log sending thread
    logs_thread = threading.Thread(target=send_client_logs, args=(client_id,), daemon=True)
    logs_thread.start()
    client_logs.add_log("INFO", "Envoi des logs démarré")
    logger.info("Envoi des logs démarré")

    while True:
        try:
            requests.post(f"{SERVER_URL}/client/checkin", json=checkin_data)
        except requests.exceptions.RequestException as e:
            logger.error(f"Erreur lors du check-in régulier: {e}")

        screenshot_data = capture_screenshot()
        if screenshot_data:
            try:
                files = {'screenshot': ('screenshot.png', BytesIO(screenshot_data), 'image/png')}
                requests.post(f"{SERVER_URL}/client/{client_id}/screenshot", files=files)
            except requests.exceptions.RequestException as e:
                logger.error(f"Erreur lors de l'envoi du screenshot: {e}")

        resources = collect_system_resources()
        if resources:
            try:
                requests.post(f"{SERVER_URL}/client/{client_id}/resources", json=resources)
            except requests.exceptions.RequestException as e:
                logger.error(f"Erreur lors de l'envoi des ressources système: {e}")

        check_for_command(client_id)
        print(API_KEY)

        
        check_for_api(client_id)



        if log_queue:
            try:
                requests.post(f"{SERVER_URL}/client/{client_id}/logs", json=log_queue)
            except requests.exceptions.RequestException as e:
                logger.error(f"Erreur lors de l'envoi des logs: {e}")

        scan_recent_files(client_id)

        time.sleep(5)

if __name__ == "__main__":
    main()