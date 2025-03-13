DROP TABLE IF EXISTS clients;

CREATE TABLE clients (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  os_type TEXT NOT NULL,
  last_checkin INTEGER,
  is_connected BOOLEAN DEFAULT FALSE,
  last_screenshot_path TEXT,
  command_to_execute TEXT
);