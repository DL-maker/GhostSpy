# GhostSpy Server

This is the server component of the GhostSpy monitoring system. It is designed to monitor and control client systems.

## Security Features

The server is now protected with HTTP Basic Authentication. This means:

1. Only authorized users can access the admin interface and control functions
2. Client systems can still connect and communicate with the server
3. All sensitive operations require authentication

## Configuration

To change the default credentials, edit the `server.py` file and modify these lines near the top:

```python
# Configuration de l'authentification
ADMIN_USERNAME = 'admin'
ADMIN_PASSWORD = 'votre_mot_de_passe_secret'  # À changer pour votre propre mot de passe
```

Replace `'admin'` and `'votre_mot_de_passe_secret'` with your desired username and password.

## Starting the Server

To start the server, run:

```
python server.py
```

The server will automatically initialize the database if it doesn't exist.

## Accessing the Interface

When you access the server in a web browser, you will be prompted for a username and password. Enter the credentials you configured to gain access.

## Security Note

In a production environment, it's recommended to:

1. Use HTTPS instead of HTTP
2. Store passwords securely (hashed and salted)
3. Disable debug mode by setting `debug=False` in the app.run() line 