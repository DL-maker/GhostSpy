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