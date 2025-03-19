document.addEventListener('DOMContentLoaded', function() {
    const clientListDiv = document.getElementById('client-list');
    const devicePageDiv = document.getElementById('device-page');
    const backToListButton = document.getElementById('back-to-list-button');
    const screenshotDisplay = document.getElementById('screenshot-display');
    const deviceNameHeader = document.getElementById('device-name-header');
    const commandInput = document.getElementById('command-input');
    const executeCommandButton = document.getElementById('execute-command-button');
    const commandOutputDiv = document.getElementById('command-output');
    const connectedCountSpan = document.getElementById('connected-count');
    const disconnectedCountSpan = document.getElementById('disconnected-count');

    let currentClientId = null; // Pour suivre l'appareil actuellement affiché dans la page dédiée

    function fetchClients() {
        fetch('/clients') // Endpoint API Flask pour récupérer la liste des clients
            .then(response => response.json())
            .then(clients => {
                clientListDiv.innerHTML = ''; // Effacer la liste actuelle
                let connectedClients = 0;
                let disconnectedClients = 0;

                clients.forEach(client => {
                    const clientBlock = document.createElement('div');
                    clientBlock.className = 'client-block';
                    clientBlock.innerHTML = `
                        <h3>${client.name}</h3>
                        <p>OS: ${client.os_type}</p>
                        <p>Connecté: ${client.is_connected ? 'Oui' : 'Non'}</p>
                        <button onclick="showDevicePage(${client.id}, '${client.name}')">Surveiller</button>
                        <button onclick="disconnectClient(${client.id})">Déconnecter</button> 
                    `;
                    clientListDiv.appendChild(clientBlock);
                    if (client.is_connected) {
                        connectedClients++;
                    } else {
                        disconnectedClients++;
                    }
                });
                connectedCountSpan.textContent = connectedClients;
                disconnectedCountSpan.textContent = disconnectedClients;
            });
    }

    window.showDevicePage = function(clientId, clientName) { // Fonction globale pour être appelée depuis HTML
        currentClientId = clientId;
        deviceNameHeader.textContent = clientName;
        devicePageDiv.style.display = 'block';
        clientListDiv.style.display = 'none';
        fetchScreenshot(clientId); // Charger le premier screenshot en arrivant sur la page
        startScreenshotPolling(clientId); // Démarrer le polling régulier des screenshots
    }

    window.disconnectClient = function(clientId) { // Fonction globale pour être appelée depuis HTML
fetch(`/client/${clientId}/disconnect`, { // Endpoint API Flask pour déconnecter le client
    method: 'POST',
})
.then(response => response.json())
.then(data => {
    console.log(data.message); // Afficher un message de confirmation dans la console (peut être amélioré)
    fetchClients(); // Rafraîchir la liste des clients pour mettre à jour l'état de connexion
});
}

    backToListButton.addEventListener('click', function() {
        devicePageDiv.style.display = 'none';
        clientListDiv.style.display = 'flex';
        stopScreenshotPolling(); // Arrêter le polling quand on quitte la page de l'appareil
    });

    let screenshotPollingInterval; // Variable pour stocker l'intervalle du polling des screenshots

    function fetchScreenshot(clientId) {
        screenshotDisplay.src = `/screenshots/client_${clientId}_latest.png?timestamp=${new Date().getTime()}`; // Ajout d'un timestamp pour forcer le navigateur à recharger l'image
    }


    function startScreenshotPolling(clientId) {
        screenshotPollingInterval = setInterval(() => {
            fetchScreenshot(clientId);
        }, 5000); // Rafraîchir le screenshot toutes les 5 secondes (ajustez ce délai)
    }

    function stopScreenshotPolling() {
        clearInterval(screenshotPollingInterval);
    }


    executeCommandButton.addEventListener('click', function() {
        const command = commandInput.value;
        if (command && currentClientId) {
            fetch(`/client/${currentClientId}/command`, {  // Endpoint API Flask pour exécuter une commande
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ command: command })
            })
            .then(response => response.json())
            .then(data => {
                commandOutputDiv.textContent = data.message; // Afficher la réponse du serveur
                commandInput.value = ''; // Vider l'input de commande
            });
        } else {
            commandOutputDiv.textContent = 'Veuillez entrer une commande et sélectionner un appareil.';
        }
    });


    // Rafraîchir la liste des clients toutes les 10 secondes (ou moins souvent)
    setInterval(fetchClients, 10000); // Rafraîchir la liste toutes les 10 secondes
    fetchClients(); // Charger la liste initiale au démarrage de la page
});