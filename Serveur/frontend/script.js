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
                        <h3><img src="${client.os_type}.png" alt="OS_icon" width="25" height="25"/>${client.name}</h3>
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
        fetchResourceInfo(clientId); // Charger les premières données de ressources
        startResourcePolling(clientId); // Démarrer le polling régulier des ressources
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
        stopResourcePolling(); // Arrêter le polling des ressources
    });

    let screenshotPollingInterval; // Variable pour stocker l'intervalle du polling des screenshots
    let resourcePollingInterval;

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
        // Afficher l'élément de sortie et indiquer que la commande est en cours
        const commandOutput = document.getElementById('command-output');
        commandOutput.style.display = 'block';
        commandOutput.innerHTML = `
            <div class="command-header">
                <div class="command-spinner"></div>
                Exécution de la commande: <span style="color: #38bdf8">${command}</span>
            </div>
            <p>Veuillez patienter...</p>
        `;
        
        fetch(`/client/${currentClientId}/command`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ command: command })
        })
        .then(response => response.json())
        .then(data => {
            // Attendre quelques secondes pour que la commande soit exécutée
            setTimeout(() => {
                checkCommandResult(currentClientId);
            }, 2000);
            
            commandInput.value = ''; // Vider l'input de commande
        })
        .catch(error => {
            commandOutput.innerHTML = `
                <div class="command-header" style="color: #fb7185">
                    Erreur lors de l'envoi de la commande
                </div>
                <p>${error.message || 'Une erreur est survenue'}</p>
            `;
        });
    } else {
        const commandOutput = document.getElementById('command-output');
        commandOutput.style.display = 'block';
        commandOutput.innerHTML = `
            <div class="command-header" style="color: #fb7185">
                Erreur
            </div>
            <p>Veuillez entrer une commande et sélectionner un appareil.</p>
        `;
    }
});

function checkCommandResult(clientId) {
    fetch(`/client/${clientId}/commandresult`)
    .then(response => response.json())
    .then(data => {
        const commandOutput = document.getElementById('command-output');
        
        if (data.output) {
            // Formater la sortie pour une meilleure lisibilité
            let resultHtml = `
                <div class="command-header">
                    Commande : <span style="color: #38bdf8">${data.output.command}</span>
                </div>`;
                
            // Sortie standard
            if (data.output.stdout && data.output.stdout.trim() !== '') {
                resultHtml += `
                <div>
                    <div style="color: #94a3b8; margin-top: 10px;">STDOUT :</div>
                    <pre class="command-stdout">${escapeHtml(data.output.stdout)}</pre>
                </div>`;
            } else {
                resultHtml += `<div style="color: #94a3b8; margin-top: 10px;">STDOUT : (Pas de sortie)</div>`;
            }
            
            // Erreur standard
            if (data.output.stderr && data.output.stderr.trim() !== '') {
                resultHtml += `
                <div>
                    <div style="color: #94a3b8; margin-top: 10px;">STDERR :</div>
                    <pre class="command-stderr">${escapeHtml(data.output.stderr)}</pre>
                </div>`;
            }
            
            commandOutput.innerHTML = resultHtml;
        } else {
            // Si pas de résultat encore, afficher un message et réessayer après un court délai
            commandOutput.innerHTML = `
                <div class="command-header">
                    <div class="command-spinner"></div>
                    Attente de la réponse...
                </div>
                <p>L'exécution de la commande est en cours, veuillez patienter.</p>
            `;
            setTimeout(() => checkCommandResult(clientId), 2000);
        }
    })
    .catch(error => {
        const commandOutput = document.getElementById('command-output');
        commandOutput.innerHTML = `
            <div class="command-header" style="color: #fb7185">
                Erreur lors de la récupération du résultat
            </div>
            <p>${error.message || 'Une erreur est survenue'}</p>
        `;
    });
}

// Fonction utilitaire pour échapper le HTML et éviter les injections XSS
function escapeHtml(unsafe) {
    return unsafe
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

    // Rafraîchir la liste des clients
    setInterval(fetchClients, 5000); 
    fetchClients(); 

function percentageToDegrees(percent) {
    return percent * 3.6;
}

function fetchResourceInfo(clientId) {
    fetch(`/client/${clientId}/resources`)
        .then(response => response.json())
        .then(data => {
            if (data.resources) {
                const cpuUsage = data.resources.cpu_usage;
                const ramUsage = data.resources.ram_used;
                const cpuThresholdExceeded = data.resources.cpu_threshold_exceeded;
                const ramThresholdExceeded = data.resources.ram_threshold_exceeded;

                // --- CPU Circle --- 
                const cpuCircle = document.getElementById('cpu-progress');
                const cpuPercentageText = document.getElementById('cpu-usage-text');
                const cpuAlertText = document.getElementById('cpu-alert');

                let cpuColor;
                if (cpuUsage > 80) {
                    cpuColor = '#ff3333'; 
                } else if (cpuUsage > 60) {
                    cpuColor = '#ff9933'; 
                } else {
                    cpuColor = '#4CAF50';
                }

                // Mettre à jour correctement le gradient du cercle CPU
                cpuCircle.style.background = `conic-gradient(${cpuColor} ${percentageToDegrees(cpuUsage)}deg, #e2e8f0 0deg)`;
                cpuPercentageText.textContent = cpuUsage + '%';

                if (cpuThresholdExceeded) {
                    cpuCircle.classList.add('pulse');
                    cpuAlertText.textContent = 'CPU dépasse le seuil maximal!';
                } else {
                    cpuCircle.classList.remove('pulse');
                    cpuAlertText.textContent = '';
                }

                // --- RAM Circle --- 
                const ramCircle = document.getElementById('ram-progress');
                const ramPercentageText = document.getElementById('ram-usage-text');
                const ramAlertText = document.getElementById('ram-alert');

                let ramColor;
                if (ramUsage > 80) {
                    ramColor = '#ff3333';
                } else if (ramUsage > 60) {
                    ramColor = '#ff9933';
                } else {
                    ramColor = '#4CAF50';
                }

                // Mettre à jour correctement le gradient du cercle RAM
                ramCircle.style.background = `conic-gradient(${ramColor} ${percentageToDegrees(ramUsage)}deg, #e2e8f0 0deg)`;
                ramPercentageText.textContent = ramUsage + '%';

                if (ramThresholdExceeded) {
                    ramCircle.classList.add('pulse');
                    ramAlertText.textContent = 'RAM dépasse le seuil maximal!';
                } else {
                    ramCircle.classList.remove('pulse');
                    ramAlertText.textContent = '';
                }
            }
        })
        .catch(err => {
            console.error('Error fetching resource info:', err);
        });
}

function startResourcePolling(clientId) {
    resourcePollingInterval = setInterval(() => {
        fetchResourceInfo(clientId); }, 5000); // Le Refresh
    }
    
    function stopResourcePolling() {
    clearInterval(resourcePollingInterval); }
    });