DROP TABLE IF EXISTS clients;



CREATE TABLE IF NOT EXISTS clients (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  os_type TEXT NOT NULL,
  last_checkin INTEGER,
  is_connected BOOLEAN DEFAULT FALSE,
  last_screenshot_path TEXT,
  command_to_execute TEXT,
  command_output TEXT,
  logs TEXT,
  resources TEXT,
  scan_file TEXT,
  vt_scan_results TEXT,
  malicious_files TEXT
);


ALTER TABLE clients ADD COLUMN add_api_key TEXT;

-- Table pour stocker l'historique des commandes (boutons)
CREATE TABLE IF NOT EXISTS command_history (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  client_id INTEGER NOT NULL,
  command TEXT NOT NULL,
  command_id TEXT,
  button_type TEXT, -- 'PowerOff', 'CancelShutdown', 'Freeze', 'Unfreeze', 'Manual'
  timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
  status TEXT, -- 'success', 'error', 'pending'
  stdout TEXT,
  stderr TEXT,
  FOREIGN KEY (client_id) REFERENCES clients (id)
);

-- Index pour accélérer les recherches
CREATE INDEX IF NOT EXISTS idx_history_client_id ON command_history (client_id);
CREATE INDEX IF NOT EXISTS idx_history_command_id ON command_history (command_id);
