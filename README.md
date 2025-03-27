# GhostSpy - 🌐 Outil Pédagogique d'Analyse Réseau

Un outil éducatif conçu pour comprendre le fonctionnement des réseaux informatiques et leurs vulnérabilités dans un cadre académique contrôlé.

---

## 🔬 Objectifs Pédagogiques

- 🎨 **Comprendre** les protocoles réseau et leurs mécanismes.
- 🔒 **Apprendre** les concepts de base de la sécurité réseau.
- 📊 **Étudier** les méthodes de surveillance et d'analyse de trafic.
- 💼 **Développer** des compétences en administration réseau.

---

## 🛠️ Caractéristiques Principales

### 🔌 Analyse Réseau
- Visualisation des appareils connectés avec leurs caractéristiques techniques (adresse MAC, IP, nom d'hôte).

### 🔎 Surveillance de Trafic
- Observation et analyse des flux de données pour comprendre les protocoles réseau.

### 📊 Collecte de Statistiques
- Génération de rapports sur l'utilisation du réseau et les modèles de communication.

### ⚡ Analyse de Performances
- Mesure de la latence, de la bande passante et de la qualité de connexion.

---

## 🔧 Prérequis

- 💻 **Python** 3.8 ou supérieur.
- 🔄 **Environnement Linux/Unix**.
- 🔐 **Privilèges administrateur** pour l'analyse réseau.
- 📡 **Connexion à un réseau local**.

---

## 🔄 Installation

### 1️⃣ Cloner le dépôt
Pour cloner le dépôt Git et accéder au dossier du projet, exécutez les commandes suivantes :

```bash
git clone https://github.com/DL-maker/GhostSpy.git
cd GhostSpy
```

### 2️⃣ Créer un environnement virtuel

#### Sous Linux/Mac
Pour créer et activer un environnement virtuel sous Linux/Mac, exécutez les commandes suivantes :

```bash
python -m venv venv
source venv/bin/activate
```

#### Sous Windows
Pour créer et activer un environnement virtuel sous Windows, exécutez les commandes suivantes :

```bash
python -m venv venv
.\venv\Scripts\activate
```

### 3️⃣ Installer les dépendances
Pour installer les dépendances requises pour GhostSpy, exécutez la commande suivante :

```bash
pip install -r requirements.txt
```

---

## 🔍 Guide d'Utilisation

### 🛠️ Configuration Initiale

Pour configurer l'environnement d'analyse, utilisez cette commande :

```bash
ghostspy --setup
```

Pour vérifier les prérequis système, utilisez cette commande :

```bash
ghostspy --check-requirements
```

---

### 🕵️‍♂️ Commandes de Base

#### 📡 Analyse Réseau
Pour scanner le réseau local, utilisez cette commande :

```bash
ghostspy --scan-network
```

Pour afficher les détails d'un appareil, utilisez cette commande (remplacez `<IP>` par l'adresse IP de l'appareil) :

```bash
ghostspy --device-info <IP>
```

Pour générer un rapport d'analyse, utilisez cette commande :

```bash
ghostspy --generate-report
```

#### 🔎 Surveillance du Trafic
Pour démarrer la capture de trafic, utilisez cette commande :

```bash
ghostspy --capture-traffic
```

Pour analyser les protocoles utilisés, utilisez cette commande :

```bash
ghostspy --analyze-protocols
```

Pour exporter les données collectées (formats disponibles : JSON, CSV), utilisez cette commande :

```bash
ghostspy --export-data <format>
```

---

## 📈 Bonnes Pratiques

- 🏢 **Utilisez l'outil dans un environnement contrôlé** (laboratoire dédié).
- 🖊️ **Documentez vos expériences et observations.**
- ❤️ **Respectez la vie privée et les règles de sécurité.**
- 🛡️ **N'utilisez que des données de test, jamais de données réelles.**

---

## 🔒 Cadre Légal et Éthique

- Cet outil est conçu **exclusivement pour l'apprentissage**.
- Utilisez-le uniquement dans un **environnement de laboratoire contrôlé**.
- Les tests sur des réseaux réels sont **interdits sans autorisation explicite**.
- Respectez les lois en vigueur concernant la **protection des données** et la **vie privée**.

---


