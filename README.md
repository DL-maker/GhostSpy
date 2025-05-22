# GhostSpy

## Description
GhostSpy est un outil d'administration permettant aux administrateurs système de contrôler et surveiller un parc de PC au sein d'un réseau local d'entreprise. Il offre des fonctionnalités de surveillance et de contrôle à distance pour faciliter la gestion des ordinateurs.

## Fonctionnalités principales

### Pour tous les systèmes d'exploitation
- **Exécution de commandes à distance** - Permet d'exécuter des commandes sur les machines distantes, compatible avec tous les OS.
- **Surveillance des ressources système** - Collecte et envoie des informations sur l'utilisation du CPU, de la mémoire et du disque.
- **Visualisation à distance des écrans** - Permet à l'administrateur de voir l'écran des ordinateurs surveillés.

### Fonctionnalités configurables
Ces fonctionnalités peuvent être activées ou désactivées selon les besoins :
- **Analyse VirusTotal** - Analyse des fichiers suspects avec l'API VirusTotal pour détecter les menaces potentielles.
- **Journalisation des activités** - Enregistrement des activités système comme la création, modification et suppression de fichiers.
- **Détection de fichiers suspects** - Surveillance de la création et modification de fichiers potentiellement dangereux dans les dossiers sensibles.

### Limitations selon l'OS

| Fonctionnalité | Windows | Linux | macOS |
|----------------|---------|-------|-------|
| Exécution de commandes | ✅ | ✅ | ✅ |
| Visualisation d'écran | ✅ | ✅ | ✅ |
| Freeze/Unfreeze d'écran | ✅ | ❌ | ❌ |
| Journalisation côté client | ✅ | ❌ | ❌ |

## Prérequis
- Python 3.13 ou supérieur

### Dépendances
#### Pour le serveur (server.py)
```python
from flask import Flask, json, jsonify, request, send_from_directory, Response
import sqlite3
from PIL import Image
import time
import os
import threading
from functools import wraps
```

#### Pour le client (client.py)
```python
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
import colorama
import ctypes
import customtkinter as ctk
```

## Installation
Des fichiers exécutables (.exe) sont disponibles pour le serveur et le client, sans installation supplémentaire requise.

## Configuration et utilisation

### Configuration du serveur
1. Exécutez le fichier server.exe sur l'ordinateur de l'administrateur ou un serveur dédié
2. Définissez un mot de passe pour accéder au panneau de configuration
3. Le serveur est maintenant prêt à recevoir les connexions des clients

### Configuration des clients
1. Installez et exécutez client.exe sur chaque ordinateur du parc à surveiller
2. Lorsque demandé, saisissez l'adresse IP du serveur (ordinateur administrateur)
3. Le client se connectera automatiquement au serveur

### Utilisation quotidienne
Une fois configuré, l'administrateur peut accéder au panneau de contrôle via le serveur pour surveiller et gérer tous les PC clients connectés.

## Considérations de sécurité
- GhostSpy fonctionne uniquement sur le réseau local/VLAN de l'entreprise et ne transmet pas de données à des serveurs externes
- Les données collectées et les actions effectuées sont sous la responsabilité de l'administrateur et doivent respecter les contrats de travail et les législations en vigueur
- Aucune responsabilité n'est assumée par les développeurs concernant l'utilisation abusive de l'outil

## Développements futurs
- Implémentation des fonctionnalités manquantes pour Linux et macOS

## Support
Pour toute question ou problème, veuillez utiliser les commentaires sur GitHub.

## Licence
Ce projet est sous licence GPL-3.0.


## Contributeurs
* **DL-maker**
* **BatyaBatkovich** (Lucas Daifi)
* **Thisisnnn**
* **prometeu1**