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
import ctypes    # Import ctypes for direct Windows API access
import customtkinter as ctk

# Initialize colorama
colorama.init(autoreset=True)

# Configuration
CONFIG_FILE = 'config.json'
API_KEY = "API"  # Remplacez par votre clé API VirusTotal
VT_BASE_URL = "https://www.virustotal.com/api/v3"
LOG_FILE = "client_vt.log"

# Paramètres des fonctionnalités (désactivées par défaut)
VIRUSTOTAL_ENABLED = False
ACTIVITY_LOGS_ENABLED = False
FILE_DETECTION_ENABLED = False
SYSTEM_RESOURCES_ENABLED = False

# Configuration pour la liste des dossiers à surveiller
MONITORED_FOLDERS = ["Downloads", "Documents", "Desktop", "Pictures"]

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
VT_SCAN_FOLDERS = ['Downloads']

def load_server_url():
    # charge l'url du serveur
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                config = json.load(f)
                return config.get('server_url', '')
        except json.JSONDecodeError:
            print("⚠️ Le fichier de configuration est vide ou corrompu. Réinitialisation.")
    return ""

def save_server_url(server_url):
    with open(CONFIG_FILE, 'w') as f:
        json.dump({'server_url': server_url}, f)

def try_post(url, json_data):
    try:
        return requests.post(url, json=json_data, timeout=5)
    except requests.RequestException:
        return None


class ClientInterface(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.geometry("600x400")
        self.title("Interface Client")
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.server_url = ""
        self.result = None  # This will store the valid server URL if it works

        #frame
        frame = ctk.CTkFrame(master=self)
        frame.place(relx=0.5, rely=0.5, anchor="center")
        frame.pack(pady=20, padx=40, fill="x", expand=True)

        #infos pour se connecter avec l'addresse IP
        label = ctk.CTkLabel(master=frame, text='Connexion au serveur Administrateur', font=("Geist", 16))
        label.pack(pady=12, padx=10)

        self.ip_entry = ctk.CTkEntry(master=frame, placeholder_text="IP de l'administrateur", width=300, height=40, font=("Geist", 14))
        self.ip_entry.pack(pady=12, padx=10)

        #Label qui affiche si le client va se connecter ou non
        self.label_ip = ctk.CTkLabel(master=frame, text="", font=("Geist", 18))
        self.label_ip.pack(pady=(20, 0), padx=10)

        button = ctk.CTkButton(master=frame, text='Se connecter', command=self.login, font=("Geist", 14))
        button.pack(pady=12, padx=10)

    def login(self):
        ip_input = self.ip_entry.get()
        server_url = f"http://{ip_input}:5000"
        
        #data
        client_name = platform.node()
        os_type = platform.platform()
        checkin_data = {'name': client_name, 'os_type': os_type}

        response = try_post(f"{server_url}/client/checkin", json_data=checkin_data)

        if response is None or response.status_code != 200:
            self.label_ip.configure(text="L'ip n'est pas la bonne.\n Veillez réessayer.", text_color="red")
            self.ip_entry.delete(0, "end")
            self.server_url = ""
        else:
            self.label_ip.configure(text="L'ip trouvé. Connexion.", text_color="green")
            self.result = server_url  # Save the validated server_url
            self.after(1500, self.destroy)  # Close the GUI

server_url = load_server_url()

# Si la config est non-existante, montrer le GUI
if not server_url:
    app = ClientInterface()
    app.mainloop()
    if app.result:  # Vérifie si l'ip est valide
        server_url = app.result
        save_server_url(server_url)
        print(f"\n✅ Adresse IP enregistrée : {server_url}\n")
    else:
        print("\n❌ Aucune IP valide fournie. Fermeture.\n")
        exit(1)
else:
    print(f"\n✅ Adresse IP chargée depuis {CONFIG_FILE} : {server_url}\n")

class ClientLogs:
    def __init__(self):
        self.logs = []
        self.lock = threading.Lock()
        
    def add_log(self, level, message):
        # Ne pas ajouter de log si la fonctionnalité est désactivée
        if not ACTIVITY_LOGS_ENABLED:
            return
            
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
            # Ne pas envoyer les logs si la fonctionnalité est désactivée
            if not ACTIVITY_LOGS_ENABLED:
                time.sleep(20)
                continue
                
            # Add system info to logs
            client_logs.add_log(
                "INFO",
                f"État système: CPU {psutil.cpu_percent()}%, RAM {psutil.virtual_memory().percent}%"
            )
            
            logs = client_logs.get_logs()
            if logs:
                # Send logs to server
                response = requests.post(f"{server_url}/client/{client_id}/logs", json=logs, timeout=10)
                
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

# Fonction directe pour geler l'écran (sera utilisée par la commande spéciale)
def freeze_screen(seconds=0):
    """Gel de l'écran en utilisant BlockInput. Si seconds est > 0, débloque après ce délai."""
    try:
        if platform.system() == "Windows":
            # Bloquer les entrées
            ctypes.windll.user32.BlockInput(True)
            logger.info(f"Écran gelé avec BlockInput")
            
            # Si un délai est spécifié, planifier le déblocage
            if seconds > 0:
                def unfreeze():
                    try:
                        ctypes.windll.user32.BlockInput(False)
                        logger.info(f"Écran dégelé après {seconds} secondes")
                    except Exception as e:
                        logger.error(f"Erreur lors du dégel après délai: {e}")
                
                # Créer un thread pour débloquer après le délai
                timer = threading.Timer(seconds, unfreeze)
                timer.daemon = True
                timer.start()
                
            return True
    except Exception as e:
        logger.error(f"Erreur lors du gel de l'écran: {e}")
    return False

# Fonction pour dégeler l'écran
def unfreeze_screen():
    """Débloque les entrées gelées par BlockInput"""
    try:
        if platform.system() == "Windows":
            ctypes.windll.user32.BlockInput(False)
            logger.info("Écran dégelé")
            return True
    except Exception as e:
        logger.error(f"Erreur lors du dégel de l'écran: {e}")
    return False

def execute_command(command):
    try:
        # Traitement des commandes spéciales
        command_lower = command.lower().strip()
        
        if command_lower == "freeze":
            # Gel sans limite de temps
            if freeze_screen():
                return "Écran gelé avec succès. Utilisez 'unfreeze' pour débloquer.", ""
            else:
                return None, "Échec du gel de l'écran"
        
        elif command_lower == "freeze30":
            # Gel avec délai de 30 secondes
            if freeze_screen(30):
                return "Écran gelé pour 30 secondes", ""
            else:
                return None, "Échec du gel de l'écran"
        
        elif command_lower == "unfreeze":
            # Dégel immédiat
            if unfreeze_screen():
                return "Écran dégelé avec succès", ""
            else:
                return None, "Échec du dégel de l'écran"
        
        else:
            # Exécution normale de commande système
            result = subprocess.run(command, shell=True, capture_output=True, text=True)
            return result.stdout, result.stderr
    except Exception as e:
        return None, str(e)

def check_for_command(client_id):
    try:
        response = requests.get(f"{server_url}/client/{client_id}/getcommand")
        if response.status_code == 200:
            data = response.json()
            if 'command' in data and data['command']:
                command_to_execute = data['command']
                command_id = data.get('command_id')
                logger.info(f"Commande reçue du serveur: {command_to_execute} (ID: {command_id})")
                stdout, stderr = execute_command(command_to_execute)
                result = {
                    'stdout': stdout,
                    'stderr': stderr,
                    'command': command_to_execute,
                    'command_id': command_id
                }
                requests.post(f"{server_url}/client/{client_id}/commandresult", json=result)
    except Exception as e:
        logger.error(f"Erreur lors de la vérification des commandes: {e}")

def change_api(api):
    global API_KEY
    API_KEY = api
    print("Clé API mise à jour:", API_KEY)
    return API_KEY

    
def check_for_api(client_id):
    try:
        response = requests.get(f"{server_url}/client/{client_id}/token")
      
        if response.status_code == 200:
            data = response.json()
            if 'api' in data and data['api']:
                api_to_execute = data['api']
                logger.info(f"Api reçue du serveur: {api_to_execute}")
                key = change_api(api_to_execute)
                result = {'stdout': "API key updated successfully", 'stderr': "", 'command': "update_api_key"}
                requests.post(f"{server_url}/client/{client_id}/commandresult", json=result)
    except Exception as e:
        logger.error(f"Erreur lors de la vérification API: {e}")

# Fonction pour récupérer et mettre à jour les paramètres du client
def update_client_settings(client_id):
    try:
        response = requests.get(f"{server_url}/client/settings?client_id={client_id}", timeout=10)
        if response.status_code == 200:
            settings = response.json()
            
            global VIRUSTOTAL_ENABLED, ACTIVITY_LOGS_ENABLED, FILE_DETECTION_ENABLED, SYSTEM_RESOURCES_ENABLED
            
            VIRUSTOTAL_ENABLED = settings.get('virustotal_enabled', False)
            ACTIVITY_LOGS_ENABLED = settings.get('activity_logs_enabled', False)
            FILE_DETECTION_ENABLED = settings.get('file_detection_enabled', False)
            SYSTEM_RESOURCES_ENABLED = settings.get('system_resources_enabled', False)
            
            logger.info(f"Paramètres mis à jour: VT={VIRUSTOTAL_ENABLED}, Logs={ACTIVITY_LOGS_ENABLED}, "
                        f"FileDet={FILE_DETECTION_ENABLED}, SysRes={SYSTEM_RESOURCES_ENABLED}")
            print(colorama.Fore.GREEN + "✅ Paramètres mis à jour depuis le serveur")
            return True
        else:
            logger.warning(f"Erreur lors de la récupération des paramètres: {response.status_code}")
            return False
    except Exception as e:
        logger.error(f"Erreur lors de la mise à jour des paramètres: {e}")
        return False

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
    # Ne pas analyser le fichier si la fonctionnalité VirusTotal est désactivée
    if not VIRUSTOTAL_ENABLED:
        logger.info(f"Analyse VirusTotal désactivée, fichier ignoré: {os.path.basename(file_path)}")
        return
        
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
        response = requests.post(f"{server_url}/client/{client_id}/scan_file", json=scan_result)
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
        self.handle_event("moved", event.src_path, dest_path=event.dest_path)
        
    def handle_event(self, event_type, src_path, dest_path=None):
        # Ne pas traiter les événements si la fonctionnalité de logs d'activité est désactivée
        if not ACTIVITY_LOGS_ENABLED:
            return
            
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

        # Seulement scanner les fichiers si la détection de fichiers et VirusTotal sont activés
        if (not FILE_DETECTION_ENABLED) or (not VIRUSTOTAL_ENABLED):
            return
            
        # Only scan files in Downloads folder with VirusTotal
        if (event_type in ["created", "modified"]) and not is_directory and os.path.exists(src_path):
            file_ext = os.path.splitext(src_path)[1].lower()
            file_mod_time = os.path.getmtime(src_path)
            time_threshold = time.time() - (RECENT_THRESHOLD_MINUTES * 60)
            
            # Check if the file is in Downloads folder
            is_in_downloads = DOWNLOADS_FOLDER in src_path
            
            if file_mod_time >= time_threshold and file_ext in MONITORED_EXTENSIONS and is_in_downloads:
                self.scan_file(src_path)
                
    def scan_file(self, file_path):
        # Seulement scanner le fichier si les fonctionnalités sont activées
        if VIRUSTOTAL_ENABLED and FILE_DETECTION_ENABLED:
            analyze_file_with_vt(file_path, self.client_id)

def scan_recent_files(client_id, minutes=RECENT_THRESHOLD_MINUTES, max_files=5):
    # Ne pas scanner les fichiers récents si la fonctionnalité est désactivée
    if not FILE_DETECTION_ENABLED or not VIRUSTOTAL_ENABLED:
        return {"scanned": 0, "message": "File detection disabled"}
        
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
        response = requests.post(f"{server_url}/client/checkin", json=checkin_data)
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

    # Récupération initiale des paramètres
    update_client_settings(client_id)

    log_queue = []
    event_handler = None
    observer = None

    # Observer pour la surveillance des fichiers (sera démarré/arrêté selon les paramètres)
    def setup_file_monitoring():
        nonlocal observer, event_handler, log_queue
        if ACTIVITY_LOGS_ENABLED:
            if observer is None:
                event_handler = EventHandler(log_queue, client_id)
                observer = Observer()
                for folder_name in MONITORED_FOLDERS:
                    user_folder = os.path.join(os.path.expanduser("~"), folder_name)
                    if os.path.exists(user_folder):
                        observer.schedule(event_handler, path=user_folder, recursive=True)
                        logger.info(f"Surveillance du dossier {folder_name}: {user_folder}")
                    else:
                        logger.warning(f"Le dossier {folder_name} est introuvable.")
                observer.start()
                logger.info("Surveillance des fichiers démarrée")
                return True
            return True
        else:
            if observer is not None:
                observer.stop()
                observer.join()
                observer = None
                logger.info("Surveillance des fichiers arrêtée")
            return False
    
    setup_file_monitoring()
    
    # Thread pour l'envoi des logs (sera démarré uniquement si ACTIVITY_LOGS_ENABLED)
    logs_thread = None
    if ACTIVITY_LOGS_ENABLED:
        logs_thread = threading.Thread(target=send_client_logs, args=(client_id,), daemon=True)
        logs_thread.start()
        client_logs.add_log("INFO", "Envoi des logs démarré")
        logger.info("Envoi des logs démarré")
    
    settings_update_counter = 0
    settings_update_interval = 12  # Vérifier les paramètres toutes les 12 itérations (environ 1 minute)
    
    while True:
        try:
            # Check-in régulier avec le serveur
            requests.post(f"{server_url}/client/checkin", json=checkin_data)
        except requests.exceptions.RequestException as e:
            logger.error(f"Erreur lors du check-in régulier: {e}")

        # Capture et envoi de screenshot (toujours actif)
        screenshot_data = capture_screenshot()
        if screenshot_data:
            try:
                files = {'screenshot': ('screenshot.png', screenshot_data, 'image/png')}
                requests.post(f"{server_url}/client/{client_id}/screenshot", files=files)
            except requests.exceptions.RequestException as e:
                logger.error(f"Erreur lors de l'envoi du screenshot: {e}")

        # Collecte et envoi des ressources système (conditionnel)
        if SYSTEM_RESOURCES_ENABLED:
            resources = collect_system_resources()
            if resources:
                try:
                    requests.post(f"{server_url}/client/{client_id}/resources", json=resources)
                    logger.debug("Ressources système envoyées")
                except requests.exceptions.RequestException as e:
                    logger.error(f"Erreur lors de l'envoi des ressources: {e}")
        else:
            logger.debug("L'envoi des ressources système est désactivé")

        # Vérification des commandes (toujours actif)
        check_for_command(client_id)
        
        # Vérification de l'API VirusTotal (toujours actif pour la récupération de clé)
        check_for_api(client_id)

        # Envoi des logs de surveillance de fichiers (conditionnel)
        if ACTIVITY_LOGS_ENABLED and log_queue:
            # La logique d'envoi est gérée par le thread
            pass
        else:
            logger.debug("L'envoi des logs d'activité est désactivé")

        # Scan des fichiers récents (conditionnel)
        if FILE_DETECTION_ENABLED and VIRUSTOTAL_ENABLED:
            # Exécuter la logique de scan VirusTotal ici
            logger.debug("Scan des fichiers suspects actif")
        else:
            logger.debug("Le scan des fichiers suspects est désactivé")
            
        # Mise à jour périodique des paramètres
        settings_update_counter += 1
        if settings_update_counter >= settings_update_interval:
            old_activity_logs = ACTIVITY_LOGS_ENABLED
            
            update_client_settings(client_id)
            settings_update_counter = 0
            
            # Si le paramètre ACTIVITY_LOGS_ENABLED a changé, reconfigurer la surveillance
            if old_activity_logs != ACTIVITY_LOGS_ENABLED:
                setup_file_monitoring()
                
                # Redémarrer le thread d'envoi des logs si nécessaire
                if ACTIVITY_LOGS_ENABLED and (logs_thread is None or not logs_thread.is_alive()):
                    logs_thread = threading.Thread(target=send_client_logs, args=(client_id,), daemon=True)
                    logs_thread.start()
                    client_logs.add_log("INFO", "Envoi des logs redémarré")
                    logger.info("Envoi des logs redémarré")

        time.sleep(5)

if __name__ == "__main__":
    main()