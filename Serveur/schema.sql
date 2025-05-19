-- Schéma de la base de données pour l'application SpyGhost

-- Table des clients
DROP TABLE IF EXISTS clients;
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

-- Table de l'historique des commandes
DROP TABLE IF EXISTS command_history;
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
