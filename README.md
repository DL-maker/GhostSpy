# GhostSpy

## Description générale
*GhostSpy* est un outil d'administration conçu pour donner à un administrateur le contrôle complet sur un parc de PC. Il fonctionne dans un réseau local/VLAN d'entreprise ou domestique.
## Fonctionnalités principales

### Contrôle et surveillance (Windows uniquement)
- **Visualisation d'écran à distance** - Permet à l'administrateur de voir l'écran des postes clients en temps réel
- **Exécution de commandes à distance** - Autorise le lancement de commandes sur les postes clients
- **Gel d'écran (Freeze/Unfreeze)** - Capacité à figer temporairement l'écran des utilisateurs

### Surveillance de sécurité (compatibilité variable selon OS)
- **Analyse VirusTotal** - Analyse des fichiers suspects via l'API VirusTotal pour détecter les menaces potentielles
- **Journalisation des activités** - Enregistrement des actions comme la création, modification et suppression de fichiers
- **Détection de fichiers suspects** - Surveillance de la création et modification de fichiers potentiellement dangereux dans les dossiers sensibles
- **Surveillance des ressources système** - Collecte et envoi d'informations sur l'utilisation du CPU, de la mémoire et du disque

## Compatibilité des systèmes d'exploitation

| Fonctionnalité                  | Windows | Linux | macOS |
| ------------------------------- | ------- | ----- | ----- |
| Surveillance d'écran à distance | ✅       | ❌     | ✅     |
| Exécution de commandes          | ✅       | ✅     | ✅     |
| Freeze/Unfreeze                 | ✅       | ❌     | ❌     |
| Journalisation côté client      | ✅       | ❌     | ❌     |
| Autres fonctionnalités          | ✅       | ✅     | ✅     |

___
### ⚠️ **Note importante** : On ne prend aucune responsabilité si l'outil est utilisé à mauvais escient. ⚠️

___
## Prérequis
- Python 3.13 minimum

### Bibliothèques nécessaires
#### Pour le serveur (server.py)
```python
flask>=2.3.0
Pillow>=10.0.0
customtkinter>=5.2.0
```

#### Pour le client (client.py)
```python
requests>=2.31.0
Pillow>=10.0.0
psutil>=5.9.5
watchdog>=3.0.0
colorama>=0.4.6
customtkinter>=5.2.0
```

___
## Installation
Des [fichiers exécutables](https://github.com/DL-maker/GhostSpy/tree/main/Executables) (.exe) sont disponibles pour le serveur et le client, ne nécessitant pas d'installation manuelle des dépendances.

## Configuration et démarrage

### Côté serveur (administrateur)
1. Faire un copie du server.exe (qui ce trouve dans dossier ./Executable)
2. Exécutez le fichier server.exe sur le PC administrateur ou le serveur dédié 
3. Définissez un mot de passe pour accéder au panneau de configuration

### Côté client
1. Faire un copie du server.exe (qui ce trouve dans dossier ./Executable)
2. Mettre le fichier client.exe avec le requirements.txt dans le C:\Users\LD\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup ou Win + R => shell:startup
3. Redemarer le PC
4. Lors du démarrage, entrez l'adresse IP du serveur administrateur

## Utilisation quotidienne
Une fois le serveur et les clients configurés, l'administrateur peut:
- Surveiller les écrans des PC clients en temps réel
- Exécuter des commandes à distance
- Geler/dégeler les écrans des utilisateurs (Windows uniquement)
- Surveiller les activités suspectes et les ressources système
- Analyser les fichiers suspects avec VirusTotal

## Considérations de sécurité
- GhostSpy fonctionne uniquement au sein du réseau local/VLAN de l'entreprise
- Aucune donnée n'est envoyée à des serveurs externes
- L'utilisation de GhostSpy doit respecter les contrats de travail et les législations en vigueur
- Nous ne sommes pas responsables d'une utilisation abusive de l'outil, du non-respect des contrats ou de la violation de la vie privée d'une personne

## Limitations connues
- Certaines fonctionnalités ne sont pas disponibles sur tous les systèmes d'exploitation (voir tableau de compatibilité)

## Développements futurs
- Amélioration de la compatibilité avec Linux et macOS pour toutes les fonctionnalités
- Mise en place d'une page englobant tous les logs

---
## Support
Pour toute question ou signalement de bug, veuillez utiliser la section des commentaires sur GitHub.