document.addEventListener('DOMContentLoaded', function() {
    console.log("DOM Content Loaded - Initializing Application");
    const clientListDiv = document.getElementById('client-list');
    const devicePageDiv = document.getElementById('device-page');
    const backToListButton = document.getElementById('back-to-list-button');
    const screenshotDisplay = document.getElementById('screenshot-display');
    const deviceNameHeader = document.getElementById('device-name-header');
    const commandInput = document.getElementById('command-input');
    const executeCommandButton = document.getElementById('execute-command-button');
    const PowerOffCommandButton = document.getElementById('PowerOff-command-button');
    const executeAPIbutton = document.getElementById('execute-api-button');
    const commandOutputDiv = document.getElementById('command-output');
    const connectedCountSpan = document.getElementById('connected-count');
    const disconnectedCountSpan = document.getElementById('disconnected-count');
    const apiInput = document.getElementById('api-input');

    // Set up global client ID to be accessible from all functions
    window.currentClientId = null;
    let screenshotPollingInterval;
    let resourcePollingInterval;
    let logsPollingInterval;
    let scanResultsPollingInterval;
    let lastProcessedLogTime = null;
    let lastCommandIdSent = null;
    
    // Initialize global window functions for direct onclick access from HTML
    window.executeCommand = function() {
        const commandInputElem = document.getElementById('command-input');
        const command = commandInputElem.value;
        if (!command) {
            return; // Ne rien faire si aucune commande n'est entrée
        }
        
        if (!window.currentClientId) {
            const commandOutput = document.getElementById('command-output');
            commandOutput.style.display = 'block';
            commandOutput.innerHTML = `
                <div class="command-header" style="color: #fb7185">Action impossible</div>
                <p>Sélectionnez un appareil dans la liste.</p>
            `;
            return;
        }
        
        console.log("Exécution de la commande: " + command);
        sendCommandWithButton(window.currentClientId, command, 'Manual');
        commandInputElem.value = '';
    };

    window.handlePowerOff = function() {
        if (!window.currentClientId) {
            alert("Veuillez d'abord sélectionner un appareil");
            return;
        }
        
        if (confirm("Voulez-vous vraiment éteindre cet appareil?")) {
            const commandOutput = document.getElementById('command-output');
            commandOutput.style.display = 'block';
            commandOutput.innerHTML = `
                <div class="command-header">
                    <div class="command-spinner"></div>
                    Extinction de l'appareil...
                </div>
                <p>Veuillez patienter...</p>
            `;
            
            fetch(`/client/${window.currentClientId}`, {
                credentials: 'include'
            })
                .then(response => response.json())
                .then(clientData => {
                    const osType = clientData.os_type;
                    
                    let powerOffCommand;
                    switch (osType) {
                        case "Windows":
                            powerOffCommand = "shutdown /s /t 30 /c \"Arrêt à distance demandé par Ghost Spy - Vous avez 30 secondes pour annuler avec 'shutdown /a'\"";
                            break;
                        case "Linux":
                            powerOffCommand = "sudo shutdown -h +0.5 \"Arrêt à distance demandé par Ghost Spy - Vous avez 30 secondes pour annuler\"";
                            break;
                        case "Darwin": // macOS
                            powerOffCommand = "sudo shutdown -h +0.5";
                            break;
                        default:
                            powerOffCommand = "shutdown /s /t 30";
                    }
                    
                    sendCommandWithButton(window.currentClientId, powerOffCommand, "PowerOff");
                })
                .catch(error => {
                    console.error("Erreur lors de la récupération des données client:", error);
                    commandOutput.innerHTML = `
                        <div class="command-header" style="color: #fb7185">
                            Erreur lors de la récupération des données client
                        </div>
                        <p>${error.message || 'Une erreur est survenue'}</p>
                    `;
                });
        }
    };

    window.handleCancelShutdown = function() {
        if (!window.currentClientId) {
            alert("Veuillez d'abord sélectionner un appareil");
            return;
        }
        
        const commandOutput = document.getElementById('command-output');
        commandOutput.style.display = 'block';
        commandOutput.innerHTML = `
            <div class="command-header">
                <div class="command-spinner"></div>
                Annulation de l'extinction...
            </div>
            <p>Veuillez patienter...</p>
        `;
        
        fetch(`/client/${window.currentClientId}`, {
            credentials: 'include'
        })
            .then(response => response.json())
            .then(clientData => {
                const osType = clientData.os_type;
                let cancelCommand;
                
                switch (osType) {
                    case "Windows":
                        cancelCommand = "shutdown /a";
                        break;
                    case "Linux":
                        cancelCommand = "sudo shutdown -c \"Arrêt système annulé\"";
                        break;
                    case "Darwin": // macOS
                        cancelCommand = "sudo killall shutdown";
                        break;
                    default:
                        cancelCommand = "shutdown /a";
                }
                
                sendCommandWithButton(window.currentClientId, cancelCommand, "CancelShutdown");
            })
            .catch(error => {
                console.error("Erreur lors de la récupération des données client:", error);
                commandOutput.innerHTML = `
                    <div class="command-header" style="color: #fb7185">
                        Erreur lors de la récupération des données client
                    </div>
                    <p>${error.message || 'Une erreur est survenue'}</p>
                `;
            });
    };

    window.handleFreeze = function() {
        if (!window.currentClientId) {
            alert("Veuillez d'abord sélectionner un appareil");
            return;
        }
        sendCommandWithButton(window.currentClientId, "freeze", "Freeze");
    };

    window.handleUnfreeze = function() {
        if (!window.currentClientId) {
            alert("Veuillez d'abord sélectionner un appareil");
            return;
        }
        sendCommandWithButton(window.currentClientId, "unfreeze", "Unfreeze");
    };

    window.handleGeneratePDF = function() {
        if (!window.currentClientId) {
            alert("Veuillez d'abord sélectionner un appareil");
            return;
        }
        
        // Hide download button while generating
        const downloadButton = document.getElementById('Download-PDF-button');
        downloadButton.style.display = 'none';
        
        const commandOutput = document.getElementById('command-output');
        commandOutput.style.display = 'block';
        commandOutput.innerHTML = `
            <div class="command-header">
                <div class="command-spinner"></div>
                Génération du rapport PDF...
            </div>
            <p>Veuillez patienter, cette opération peut prendre plusieurs minutes.</p>
        `;
        
        fetch(`/client/${window.currentClientId}/generate_pdf`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            credentials: 'include'
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`Erreur ${response.status}: ${response.statusText}`);
            }
            return response.json();
        })
        .then(data => {
            // Commencer à vérifier l'état du PDF
            commandOutput.innerHTML = `
                <div class="command-header">
                    <div class="command-spinner"></div>
                    Génération du rapport PDF en cours...
                </div>
                <p>Le client est en train de générer le rapport, veuillez patienter...</p>
            `;
            
            // Attendre un moment avant de commencer à vérifier
            setTimeout(() => {
                checkPDFGenerationStatus(window.currentClientId);
            }, 3000);
        })
        .catch(error => {
            console.error("Erreur lors de la demande de génération PDF:", error);
            commandOutput.innerHTML = `
                <div class="command-header" style="color: #fb7185">
                    Erreur de communication
                </div>
                <p>${error.message || 'Une erreur est survenue lors de la demande de génération'}</p>
                <button id="retry-pdf-button" class="retry-button">Réessayer</button>
            `;
            
            document.getElementById('retry-pdf-button').addEventListener('click', function() {
                handleGeneratePDF();
            });
        });
    };

    // Nouvelle fonction pour télécharger directement le PDF
    window.downloadLatestPDF = function() {
        if (!window.currentClientId) {
            alert("Veuillez d'abord sélectionner un appareil");
            return;
        }
        
        // On tente de récupérer les chemins PDF possibles
        fetch(`/client/${window.currentClientId}/check_pdf_exists`, {
            credentials: 'include',
            headers: {
                'Cache-Control': 'no-cache, no-store, must-revalidate'
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.exists) {
                // Si le PDF existe, on l'ouvre dans un nouvel onglet
                const downloadUrl = `/client/${window.currentClientId}/download_pdf?t=${new Date().getTime()}`;
                window.open(downloadUrl, '_blank');
                
                const commandOutput = document.getElementById('command-output');
                commandOutput.innerHTML = `
                    <div class="command-header" style="color: #10b981">Téléchargement lancé</div>
                    <p>Le rapport PDF est en cours de téléchargement. Vérifiez vos téléchargements.</p>
                `;
            } else {
                // Si le PDF n'existe pas selon l'API, on tente quand même le téléchargement direct
                const downloadUrl = `/client/${window.currentClientId}/download_pdf?t=${new Date().getTime()}`;
                
                fetch(downloadUrl, {
                    method: 'HEAD',
                    credentials: 'include'
                })
                .then(response => {
                    if (response.ok) {
                        window.open(downloadUrl, '_blank');
                        
                        const commandOutput = document.getElementById('command-output');
                        commandOutput.innerHTML = `
                            <div class="command-header" style="color: #10b981">Téléchargement lancé</div>
                            <p>Le rapport PDF est en cours de téléchargement. Vérifiez vos téléchargements.</p>
                        `;
                    } else {
                        // Le PDF n'existe vraiment pas
                        const commandOutput = document.getElementById('command-output');
                        commandOutput.innerHTML = `
                            <div class="command-header" style="color: #fb7185">PDF non disponible</div>
                            <p>Le fichier PDF n'est pas disponible. Veuillez réessayer de le générer.</p>
                            <button id="retry-pdf-button" class="retry-button">Générer à nouveau</button>
                        `;
                        
                        document.getElementById('retry-pdf-button').addEventListener('click', function() {
                            handleGeneratePDF();
                        });
                    }
                })
                .catch(error => {
                    console.error("Erreur lors de la vérification du téléchargement:", error);
                    // On tente quand même d'ouvrir le PDF
                    window.open(downloadUrl, '_blank');
                });
            }
        })
        .catch(error => {
            console.error("Erreur lors de la vérification de l'existence du PDF:", error);
            // En cas d'erreur, on tente quand même le téléchargement direct
            const downloadUrl = `/client/${window.currentClientId}/download_pdf?t=${new Date().getTime()}`;
            window.open(downloadUrl, '_blank');
        });
    };

    // Expose the currentClientId to global scope so HTML onclick handlers can access it
    window.getCurrentClientId = function() {
        return window.currentClientId;
    };

    function fetchClients() {
        fetch('/clients', {
            credentials: 'include'
        })
            .then(response => response.json())
            .then(clients => {
                clientListDiv.innerHTML = '';
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
                os_computer = client.os_type;
                });
                connectedCountSpan.textContent = connectedClients;
                disconnectedCountSpan.textContent = disconnectedClients;
            })
            .catch(error => console.error('Error fetching clients:', error));
    }

    window.showDevicePage = function(clientId, clientName) {
        window.currentClientId = clientId;
        deviceNameHeader.textContent = clientName;
        devicePageDiv.style.display = 'block';
        clientListDiv.style.display = 'none';
        fetchScreenshot(clientId);
        startScreenshotPolling(clientId);
        fetchResourceInfo(clientId);
        startResourcePolling(clientId);
        startLogsPolling(clientId);
        fetchScanResults(clientId);  // Fetch scan results
        startScanResultsPolling(clientId); // Start polling for scan results
        loadCommandHistory(clientId); // Charger l'historique des commandes
        lastProcessedLogTime = null;
        
        // Stockage de l'ID client dans le localStorage pour persistance
        localStorage.setItem('currentClientId', clientId);
        localStorage.setItem('currentClientName', clientName);
        
        // Activer les boutons de commande
        enableCommandButtons();

        // Fetch and apply client settings
        fetch(`/client/${clientId}/settings/admin`, {
            credentials: 'include'
        })
            .then(response => response.json())
            .then(settings => {
                applyFeatureVisibility(settings);
            })
            .catch(error => {
                console.error("Erreur lors de la récupération des paramètres:", error);
            });
    }

    // Fonction pour activer/désactiver les boutons de commande en fonction de la sélection d'appareil
    function enableCommandButtons() {
        const commandButtons = document.querySelectorAll('.command-buttons button');
        const executeCommandButton = document.getElementById('execute-command-button');
        
        if (window.currentClientId) {
            commandButtons.forEach(button => {
                button.disabled = false;
            });
            executeCommandButton.disabled = false;
        } else {
            commandButtons.forEach(button => {
                button.disabled = true;
            });
            executeCommandButton.disabled = true;
        }
    }
    
    window.disconnectClient = function(clientId) {
        fetch(`/client/${clientId}/disconnect`, {
            method: 'POST',
            credentials: 'include'
        })
        .then(response => response.json())
        .then(data => {
            console.log(data.message);
            fetchClients();
        })
        .catch(error => console.error('Error disconnecting client:', error));
    }

    backToListButton.addEventListener('click', function() {
        devicePageDiv.style.display = 'none';
        clientListDiv.style.display = 'flex';
        stopScreenshotPolling();
        stopResourcePolling();
        stopLogsPolling();
        stopScanResultsPolling(); // Stop polling for scan results
        
        // Effacer les données stockées pour éviter toute restauration future
        localStorage.removeItem('currentClientId');
        localStorage.removeItem('currentClientName');
    });

    function fetchScreenshot(clientId) {
        screenshotDisplay.src = `/screenshots/client_${clientId}_latest.png?timestamp=${new Date().getTime()}`;
    }

    function startScreenshotPolling(clientId) {
        screenshotPollingInterval = setInterval(() => {
            fetchScreenshot(clientId);
        }, 5000);
    }

    function stopScreenshotPolling() {
        clearInterval(screenshotPollingInterval);
    }

    function generateCommandId() {
        return Date.now().toString() + Math.floor(Math.random() * 10000).toString();
    }

    // Fonction améliorée pour envoyer une commande avec un bouton
    function sendCommandWithButton(clientId, command, buttonType) {
        if (!clientId) {
            // Afficher un message d'erreur dans la console et dans l'UI
            console.error("ID client non défini");
            const commandOutput = document.getElementById('command-output');
            commandOutput.style.display = 'block';
            commandOutput.innerHTML = `
                <div class="command-header" style="color: #fb7185">Erreur d'exécution</div>
                <p>Aucun client sélectionné. Veuillez choisir un appareil dans la liste.</p>
            `;
            return false;
        }
        
        // Afficher l'interface de traitement
        const commandOutput = document.getElementById('command-output');
        commandOutput.style.display = 'block';
        
        // Générer un nouvel ID unique pour cette commande
        const commandId = generateCommandId();
        lastCommandIdSent = commandId;
        
        // Mettre à jour l'interface pour montrer que la commande est en cours d'exécution
        commandOutput.innerHTML = `
            <div class="command-header">
                <div class="command-spinner"></div>
                <span>Exécution de la commande: <span style="color: #38bdf8; margin-left: 5px;">${command}</span></span>
            </div>
            <p>Veuillez patienter...</p>
        `;

        // Envoyer la commande au serveur
        console.log(`Envoi de la commande "${command}" (ID: ${commandId}, Type: ${buttonType}) au client ${clientId}`);
        
        fetch(`/client/${clientId}/command`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ 
                command: command, 
                command_id: commandId,
                button_type: buttonType 
            }),
            credentials: 'include' // Important pour inclure les cookies
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`Erreur réseau: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            console.log("Commande envoyée avec succès:", data);
            // Vérifier le résultat après un court délai
            setTimeout(() => {
                checkCommandResult(clientId);
            }, 2000);
        })
        .catch(error => {
            console.error("Erreur lors de l'envoi de la commande:", error);
            commandOutput.innerHTML = `
                <div class="command-header" style="color: #fb7185">Erreur lors de l'envoi de la commande</div>
                <p>${error.message || 'Une erreur est survenue'}</p>
            `;
        });
        
        return true;
    }

    // Fonction pour récupérer l'historique des commandes
    function fetchCommandHistory(clientId, buttonType = null) {
        if (!clientId) {
            return;
        }
        
        let url = `/client/${clientId}/command_history`;
        if (buttonType) {
            url += `?button_type=${buttonType}`;
        }
        
        return fetch(url, {
            credentials: 'include'
        })
            .then(response => {
                if (!response.ok) {
                    throw new Error(`Erreur réseau: ${response.status}`);
                }
                return response.json();
            });
    }

    function checkCommandResult(clientId) {
        fetch(`/client/${clientId}/commandresult`, {
            credentials: 'include'
        })
        .then(response => response.json())
        .then(data => {
            const commandOutput = document.getElementById('command-output');
            if (data.output && data.output.command_id === lastCommandIdSent) {
                let resultHtml = `
                    <div class="command-header">Commande : <span style="color: #38bdf8; margin-left: 5px;">${data.output.command}</span></div>`;

                if (data.output.stdout && data.output.stdout.trim() !== '') {
                    resultHtml += `
                        <div><div style="color: #94a3b8; margin-top: 10px; font-weight: bold;">STDOUT :</div><pre class="command-stdout">${escapeHtml(data.output.stdout)}</pre></div>`;
                } else {
                    resultHtml += `<div style="color: #94a3b8; margin-top: 10px; font-weight: bold;">STDOUT : (Pas de sortie)</div>`;
                }

                if (data.output.stderr && data.output.stderr.trim() !== '') {
                    resultHtml += `
                        <div><div style="color: #94a3b8; margin-top: 10px; font-weight: bold;">STDERR :</div><pre class="command-stderr">${escapeHtml(data.output.stderr)}</pre></div>`;
                }

                commandOutput.innerHTML = resultHtml;
            } else {
                commandOutput.innerHTML = `
                    <div class="command-header">
                        <div class="command-spinner"></div>
                        Attente de la réponse...
                    </div>
                    <p>L'exécution de la commande est en cours, veuillez patienter.</p>
                `;
                setTimeout(() => checkCommandResult(clientId), 1500);
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

    function escapeHtml(unsafe) {
        if (!unsafe) return '';
        
        // Préserver les sauts de ligne tout en échappant les caractères spéciaux
        return unsafe
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;")
            .replace(/\n/g, "<br>")   // Convertir les sauts de ligne en <br>
            .replace(/\s\s/g, "&nbsp;&nbsp;"); // Préserver les espaces multiples
    }

    setInterval(fetchClients, 5000);
    fetchClients();

    function percentageToDegrees(percent) {
        return percent * 3.6;
    }

    function fetchResourceInfo(clientId) {
        fetch(`/client/${clientId}/resources`, {
            credentials: 'include'
        })
            .then(response => response.json())
            .then(data => {
                if (data.resources) {
                    const cpuUsage = data.resources.cpu_usage;
                    const ramUsage = data.resources.ram_used;
                    const cpuThresholdExceeded = data.resources.cpu_threshold_exceeded;
                    const ramThresholdExceeded = data.resources.ram_threshold_exceeded;

                    const cpuCircle = document.getElementById('cpu-progress');
                    const cpuPercentageText = document.getElementById('cpu-usage-text');
                    const cpuAlertText = document.getElementById('cpu-alert');

                    let cpuColor = cpuUsage > 80 ? '#ff3333' : cpuUsage > 60 ? '#ff9933' : '#4CAF50';
                    cpuCircle.style.background = `conic-gradient(${cpuColor} ${percentageToDegrees(cpuUsage)}deg, #e2e8f0 0deg)`;
                    cpuPercentageText.textContent = cpuUsage + '%';

                    if (cpuThresholdExceeded) {
                        cpuCircle.classList.add('pulse');
                        cpuAlertText.textContent = 'CPU dépasse le seuil maximal!';
                    } else {
                        cpuCircle.classList.remove('pulse');
                        cpuAlertText.textContent = '';
                    }

                    const ramCircle = document.getElementById('ram-progress');
                    const ramPercentageText = document.getElementById('ram-usage-text');
                    const ramAlertText = document.getElementById('ram-alert');

                    let ramColor = ramUsage > 80 ? '#ff3333' : ramUsage > 60 ? '#ff9933' : '#4CAF50';
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
            .catch(err => console.error('Error fetching resource info:', err));
    }

    function startResourcePolling(clientId) {
        resourcePollingInterval = setInterval(() => {
            fetchResourceInfo(clientId);
        }, 5000);
    }

    function stopResourcePolling() {
        clearInterval(resourcePollingInterval);
    }

    function startLogsPolling(clientId) {
        fetchLogs(clientId);
        logsPollingInterval = setInterval(() => {
            fetchLogs(clientId);
        }, 5000);
    }

    function stopLogsPolling() {
        clearInterval(logsPollingInterval);
    }

    function fetchLogs(clientId) {
        fetch(`/client/${clientId}/logs`, {
            credentials: 'include'
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`Erreur lors de la récupération des logs: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            if (data.logs && data.logs.length > 0) {
                displayLogs(data.logs);
            }
        })
        .catch(error => {
            console.error('Erreur lors de la récupération des logs:', error);
            const logsContainer = document.getElementById('logs-container');
            logsContainer.innerHTML = `<p class="error-message">Erreur lors de la récupération des logs: ${error.message}</p>`;
        });
    }

    function displayLogs(logs) {
        const logsContainer = document.getElementById('logs-container');
        
        // Trier les logs par timestamp
        logs.sort((a, b) => {
            const timeA = a.timestamp || a.time || '';
            const timeB = b.timestamp || b.time || '';
            return timeA.localeCompare(timeB);
        });
        
        if (!lastProcessedLogTime) {
            logsContainer.innerHTML = "";
        }
        
        // Filtrer les nouveaux logs
        const newLogs = logs.filter(log => {
            const logTime = log.timestamp || log.time || '';
            return !lastProcessedLogTime || logTime > lastProcessedLogTime;
        });
        
        if (newLogs.length > 0) {
            // Mettre à jour le dernier timestamp traité
            const lastLog = logs[logs.length - 1];
            lastProcessedLogTime = lastLog.timestamp || lastLog.time || '';
            
            // Créer des éléments pour chaque log
            newLogs.forEach(log => {
                const logEntry = document.createElement('div');
                logEntry.className = 'log-entry';
                
                // Déterminer le type de log (si disponible)
                if (log.message) {
                    // Format des logs système
                    logEntry.innerHTML = `
                        <span class="log-time">[${log.timestamp || ''}]</span>
                        <span class="log-level">${log.level || 'INFO'}</span>
                        <span class="log-message">${escapeHtml(log.message)}</span>
                    `;
                } else if (log.type) {
                    // Format des logs de surveillance de fichiers
                    const elementTypeClass = log.element_type ? `log-entry-${log.element_type}` : '';
                    logEntry.className = `log-entry ${elementTypeClass}`;
                    logEntry.setAttribute('data-element-type', log.element_type || '');
                    logEntry.setAttribute('data-log-type', log.type || '');
                    
                    let logContent = `
                        <span class="log-time">[${log.time || ''}]</span>
                        <span class="log-type">${log.type || ''}</span>
                        <span class="log-name">${escapeHtml(log.name || '')}</span>
                    `;
                    
                    if (log.path) {
                        logContent += `<div class="log-path">${escapeHtml(log.path)}</div>`;
                    }
                    
                    if (log.warning) {
                        logContent += `<div class="log-warning">${escapeHtml(log.warning)}</div>`;
                        logEntry.classList.add('log-entry-warning');
                    }
                    
                    if (log.dest_path) {
                        logContent += `<div class="log-path">→ ${escapeHtml(log.dest_path)}</div>`;
                    }
                    
                    logEntry.innerHTML = logContent;
                }
                
                logsContainer.appendChild(logEntry);
            });
            
            // Faire défiler vers le bas pour voir les logs les plus récents
            logsContainer.scrollTop = logsContainer.scrollHeight;
        }
    }

    function fetchScanResults(clientId) {
        fetch(`/client/${clientId}/scan_file`, {
            credentials: 'include'
        })
            .then(response => response.json())
            .then(data => {
                const container = document.getElementById('scan-results-container');
                container.innerHTML = '';

                if (!data.scan_file) {
                    container.innerHTML = '<p>Aucun fichier suspect détecté récemment</p>';
                    return;
                }

                const result = data.scan_file;
                const resultDiv = document.createElement('div');
                const isSuspicious = result.is_suspicious === true;
                
                resultDiv.className = `scan-result ${isSuspicious ? 'malicious' : 'clean'}`;
                resultDiv.innerHTML = `
                    <h4>${result.file_name || 'Fichier inconnu'} - ${isSuspicious ? '⚠️ Suspect' : '✅ Normal'}</h4>
                    <p><strong>Chemin:</strong> ${result.file_path || 'Non spécifié'}</p>
                    <p><strong>Taille:</strong> ${formatFileSize(result.file_size || 0)}</p>
                    <p><strong>Date de détection:</strong> ${new Date(result.scan_date || Date.now()).toLocaleString()}</p>
                `;
                container.appendChild(resultDiv);
            })
            .catch(error => {
                console.error('Erreur lors de la récupération des fichiers suspects:', error);
                const container = document.getElementById('scan-results-container');
                container.innerHTML = '<p>Erreur lors de la récupération des fichiers suspects</p>';
            });
    }

    function formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    function startScanResultsPolling(clientId) {
        scanResultsPollingInterval = setInterval(() => {
            fetchScanResults(clientId);
        }, 10000); // Poll every 10 seconds
    }

    function stopScanResultsPolling() {
        clearInterval(scanResultsPollingInterval);
    }

    // Add CSS for scan detection details
    const style = document.createElement('style');
    style.textContent = `
        .scan-result {
            background-color: #f8faff;
            border-radius: 8px;
            padding: 15px;
            margin-bottom: 15px;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
            border-left: 4px solid #3b82f6;
        }
        .scan-result.malicious {
            background-color: #fff5f5;
            border-left-color: #e53e3e;
        }
        .scan-result.clean {
            border-left-color: #38a169;
            background-color: #f0fff4;
        }
        .scan-result h4 {
            margin-top: 0;
            margin-bottom: 10px;
            color: #4a5568;
            font-size: 16px;
        }
        .scan-result p {
            margin: 5px 0;
            font-size: 14px;
            color: #4a5568;
        }
        .scan-result.malicious h4 {
            color: #e53e3e;
        }
        .scan-result.clean h4 {
            color: #38a169;
        }
    `;
    document.head.appendChild(style);
    
    function loadScanResults(clientId) {
        fetch(`/client/${clientId}/scan_results`, {
            credentials: 'include'
        })
            .then(response => response.json())
            .then(data => {
                const scanResultsContainer = document.getElementById('scan-results-container');
                scanResultsContainer.innerHTML = '';
                
                if (data.malicious_files && data.malicious_files.length > 0) {
                    // Display malicious files first
                    const malwareHeader = document.createElement('div');
                    malwareHeader.className = 'malware-warning';
                    malwareHeader.innerHTML = `<h4>⚠️ ${data.malicious_files.length} fichier(s) malveillant(s) détecté(s)</h4>`;
                    scanResultsContainer.appendChild(malwareHeader);
                    
                    data.malicious_files.forEach(file => {
                        const fileElement = createScanResultElement(file, true);
                        scanResultsContainer.appendChild(fileElement);
                    });
                }
                
                // Display all recent scans
                if (data.scan_results && data.scan_results.length > 0) {
                    const recentHeader = document.createElement('div');
                    recentHeader.className = 'recent-scans-header';
                    recentHeader.innerHTML = '<h4>Scans récents</h4>';
                    scanResultsContainer.appendChild(recentHeader);
                    
                    data.scan_results.forEach(file => {
                        // Avoid repeating malicious files already displayed
                        if (!file.is_malicious) {
                            const fileElement = createScanResultElement(file, false);
                            scanResultsContainer.appendChild(fileElement);
                        }
                    });
                } else {
                    scanResultsContainer.innerHTML = '<p>Aucun fichier scanné récemment</p>';
                }
            })
            .catch(error => {
                console.error('Erreur lors du chargement des résultats de scan:', error);
                document.getElementById('scan-results-container').innerHTML = 
                    '<p>Erreur lors du chargement des résultats de scan</p>';
            });
    }

    function createScanResultElement(fileData, isHighlighted) {
        const fileElement = document.createElement('div');
        fileElement.className = `scan-result ${isHighlighted ? 'malicious' : 'safe'}`;
        
        // Format the date
        const scanDate = new Date(fileData.scan_date);
        const formattedDate = scanDate.toLocaleString();
        
        // Detections
        const detections = fileData.details && fileData.details.detections ? fileData.details.detections : 0;
        const totalEngines = fileData.details && fileData.details.total ? fileData.details.total : 0;
        
        // Build the display content
        let contentHTML = `
            <div class="file-info">
                <div class="file-name">${fileData.file_name}</div>
                <div class="file-path">${fileData.path || ''}</div>
                <div class="scan-date">Scanné le: ${formattedDate}</div>
            </div>
            <div class="scan-status">
        `;
        
        if (fileData.is_malicious) {
            contentHTML += `<div class="status-icon malicious">☠️</div>
                           <div class="status-text">Malveillant (${detections}/${totalEngines})</div>`;
        } else {
            contentHTML += `<div class="status-icon safe">✅</div>
                           <div class="status-text">Sécurisé (0/${totalEngines})</div>`;
        }
        
        contentHTML += `</div>`;
        fileElement.innerHTML = contentHTML;
        
        return fileElement;
    }

    // Integrate scan results into client details view
    function loadClientDetails(clientId) {
        // ...existing code...

        // Load scan results
        loadScanResults(clientId);
        
        // Set an interval to refresh scan results periodically
        if (window.scanResultsInterval) {
            clearInterval(window.scanResultsInterval);
        }
        window.scanResultsInterval = setInterval(() => {
            loadScanResults(clientId);
        }, 30000); // Refresh every 30 seconds
    }

    // Stop the scan results interval when returning to the client list
    document.getElementById('back-to-list-button').addEventListener('click', function() {
        // ...existing code...

        // Stop the scan results update interval
        if (window.scanResultsInterval) {
            clearInterval(window.scanResultsInterval);
            window.scanResultsInterval = null;
        }
    });

    // Initialiser les boutons désactivés au démarrage
    window.addEventListener('DOMContentLoaded', function() {
        const commandButtons = document.querySelectorAll('.command-buttons button');
        const executeCommandButton = document.getElementById('execute-command-button');
        
        // Désactiver les boutons au démarrage jusqu'à ce qu'un client soit sélectionné
        commandButtons.forEach(button => {
            button.disabled = true;
        });
        executeCommandButton.disabled = true;
    });

    // Fonction pour charger et afficher l'historique des commandes
    function loadCommandHistory(clientId, buttonType = null) {
        if (!clientId) {
            return;
        }
        
        fetchCommandHistory(clientId, buttonType)
            .then(history => {
                const tbody = document.getElementById('command-history-tbody');
                tbody.innerHTML = '';
                
                if (history.length === 0) {
                    const tr = document.createElement('tr');
                    tr.innerHTML = '<td colspan="4" style="text-align: center;">Aucune commande dans l\'historique</td>';
                    tbody.appendChild(tr);
                    return;
                }
                
                history.forEach(item => {
                    const tr = document.createElement('tr');
                    
                    // Date et heure formatées
                    const date = new Date(item.timestamp);
                    const formattedDate = `${date.toLocaleDateString()} ${date.toLocaleTimeString()}`;
                    
                    // Statut avec classe CSS
                    const statusClass = `status-${item.status || 'pending'}`;
                    const statusText = item.status === 'success' ? 'Succès' : 
                                      item.status === 'error' ? 'Erreur' : 
                                      'En attente';
                    
                    // Type de bouton avec classe CSS
                    const buttonClass = `button-${item.button_type || 'Manual'}`;
                    const buttonText = item.button_type || 'Manuel';
                    
                    tr.innerHTML = `
                        <td>${formattedDate}</td>
                        <td>${item.command}</td>
                        <td><span class="button-type ${buttonClass}">${buttonText}</span></td>
                        <td><span class="${statusClass}">${statusText}</span></td>
                    `;
                    
                    tbody.appendChild(tr);
                });
            })
            .catch(error => {
                console.error('Erreur lors du chargement de l\'historique :', error);
                const tbody = document.getElementById('command-history-tbody');
                tbody.innerHTML = '<tr><td colspan="4" style="text-align: center; color: #ef4444;">Erreur lors du chargement de l\'historique</td></tr>';
            });
    }

    // Ajouter un événement pour mettre à jour l'historique quand on sélectionne un appareil
    window.showDevicePage = function(clientId, clientName) {
        window.currentClientId = clientId;
        deviceNameHeader.textContent = clientName;
        devicePageDiv.style.display = 'block';
        clientListDiv.style.display = 'none';
        fetchScreenshot(clientId);
        startScreenshotPolling(clientId);
        fetchResourceInfo(clientId);
        startResourcePolling(clientId);
        startLogsPolling(clientId);
        fetchScanResults(clientId);  // Fetch scan results
        startScanResultsPolling(clientId); // Start polling for scan results
        loadCommandHistory(clientId); // Charger l'historique des commandes
        lastProcessedLogTime = null;
        
        // Stockage de l'ID client dans le localStorage pour persistance
        localStorage.setItem('currentClientId', clientId);
        localStorage.setItem('currentClientName', clientName);
        
        // Activer les boutons de commande
        enableCommandButtons();

        // Fetch and apply client settings
        fetch(`/client/${clientId}/settings/admin`, {
            credentials: 'include'
        })
            .then(response => response.json())
            .then(settings => {
                applyFeatureVisibility(settings);
            })
            .catch(error => {
                console.error("Erreur lors de la récupération des paramètres:", error);
            });
    }

    // Ajouter les événements pour les filtres d'historique
    document.addEventListener('DOMContentLoaded', function() {
        const historyFilterButtons = document.querySelectorAll('.history-filter-btn');
        historyFilterButtons.forEach(button => {
            button.addEventListener('click', function() {
                // Mettre à jour la classe active
                historyFilterButtons.forEach(btn => btn.classList.remove('active'));
                this.classList.add('active');
                
                // Récupérer le filtre sélectionné
                const filter = this.getAttribute('data-filter');
                
                // Charger l'historique filtré
                if (window.currentClientId) {
                    if (filter === 'all') {
                        loadCommandHistory(window.currentClientId);
                    } else {
                        loadCommandHistory(window.currentClientId, filter);
                    }
                }
            });
        });
        
        // Recharger l'historique périodiquement
        setInterval(() => {
            if (window.currentClientId && devicePageDiv.style.display !== 'none') {
                const activeFilterBtn = document.querySelector('.history-filter-btn.active');
                const filter = activeFilterBtn ? activeFilterBtn.getAttribute('data-filter') : 'all';
                
                if (filter === 'all') {
                    loadCommandHistory(window.currentClientId);
                } else {
                    loadCommandHistory(window.currentClientId, filter);
                }
            }
        }, 10000); // Mise à jour toutes les 10 secondes
    });

    // Ajout du bouton pour générer un rapport PDF
    const generatePDFButton = document.getElementById('Generate-PDF-button');
    if (generatePDFButton) {
        generatePDFButton.addEventListener('click', function() {
            if (!window.currentClientId) {
                return; // Ne rien faire si aucun client n'est sélectionné
            }
            
            const commandOutput = document.getElementById('command-output');
            commandOutput.style.display = 'block';
            commandOutput.innerHTML = `
                <div class="command-header">
                    <div class="command-spinner"></div>
                    Génération du rapport PDF...
                </div>
                <p>Cette opération peut prendre quelques instants. Veuillez patienter...</p>
            `;
            
            // Envoyer la demande de génération de PDF
            fetch(`/client/${window.currentClientId}/generate_pdf`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                credentials: 'include'
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error(`Erreur réseau: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                // Vérifier périodiquement si le PDF est prêt à être téléchargé
                checkPDFGenerationStatus(window.currentClientId);
            })
            .catch(error => {
                console.error("Erreur lors de la demande de génération PDF:", error);
                commandOutput.innerHTML = `
                    <div class="command-header" style="color: #fb7185">
                        Erreur lors de la demande de génération PDF
                    </div>
                    <p>${error.message || 'Une erreur est survenue'}</p>
                `;
            });
        });
    }

    // Fonction pour vérifier si le PDF est prêt
    function checkPDFGenerationStatus(clientId) {
        const commandOutput = document.getElementById('command-output');
        const downloadButton = document.getElementById('Download-PDF-button');
        let attempts = 0;
        const maxAttempts = 15; // 15 tentatives maximum (environ 45 secondes)
        
        const checkStatus = () => {
            attempts++;
            
            // Vérifier d'abord si le fichier existe
            fetch(`/client/${clientId}/check_pdf_exists`, {
                credentials: 'include',
                headers: {
                    'Cache-Control': 'no-cache, no-store, must-revalidate'
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.exists) {
                    // Le PDF est prêt à être téléchargé
                    commandOutput.innerHTML = `
                        <div class="command-header" style="color: #10b981">PDF généré avec succès</div>
                        <p>Le rapport PDF a été généré et est prêt à être téléchargé.</p>
                    `;
                    
                    // Afficher le bouton de téléchargement
                    downloadButton.style.display = 'inline-block';
                    return;
                }
                
                // Si le fichier n'existe pas encore, on fait une requête HEAD pour vérifier
                fetch(`/client/${clientId}/download_pdf`, {
                    method: 'HEAD',
                    credentials: 'include',
                    headers: {
                        'Cache-Control': 'no-cache, no-store, must-revalidate'
                    }
                })
                .then(response => {
                    if (response.ok) {
                        // Le PDF est prêt à être téléchargé
                        commandOutput.innerHTML = `
                            <div class="command-header" style="color: #10b981">PDF généré avec succès</div>
                            <p>Le rapport PDF a été généré et est prêt à être téléchargé.</p>
                        `;
                        
                        // Afficher le bouton de téléchargement
                        downloadButton.style.display = 'inline-block';
                        
                    } else if (response.status === 404) {
                        // Le PDF n'est pas encore prêt
                        if (attempts < maxAttempts) {
                            commandOutput.innerHTML = `
                                <div class="command-header">
                                    <div class="command-spinner"></div>
                                    Génération du rapport PDF en cours...
                                </div>
                                <p>Progression: ${Math.round((attempts / maxAttempts) * 100)}%</p>
                            `;
                            setTimeout(checkStatus, 3000);
                        } else {
                            // Après le nombre maximum de tentatives, on vérifie une dernière fois
                            // et on propose quand même un bouton pour tenter le téléchargement
                            commandOutput.innerHTML = `
                                <div class="command-header" style="color: #3b82f6">Traitement terminé</div>
                                <p>Le PDF a peut-être été généré malgré l'erreur. Vous pouvez tenter de le télécharger.</p>
                                <button id="try-download-button" class="download-button">Tenter le téléchargement</button>
                            `;
                            
                            document.getElementById('try-download-button').addEventListener('click', function() {
                                downloadLatestPDF();
                            });
                            
                            // Afficher aussi le bouton standard
                            downloadButton.style.display = 'inline-block';
                        }
                    } else {
                        // Une autre erreur s'est produite mais on continue
                        if (attempts < maxAttempts) {
                            commandOutput.innerHTML = `
                                <div class="command-header">
                                    <div class="command-spinner"></div>
                                    Traitement du PDF en cours...
                                </div>
                                <p>Le serveur traite votre demande, veuillez patienter...</p>
                            `;
                            setTimeout(checkStatus, 3000);
                        } else {
                            // Même après des erreurs, on tente quand même d'afficher le bouton de téléchargement
                            commandOutput.innerHTML = `
                                <div class="command-header" style="color: #3b82f6">Traitement terminé</div>
                                <p>Le PDF a peut-être été généré malgré les erreurs. Vous pouvez tenter de le télécharger.</p>
                                <button id="try-download-button" class="download-button">Tenter le téléchargement</button>
                            `;
                            
                            document.getElementById('try-download-button').addEventListener('click', function() {
                                downloadLatestPDF();
                            });
                            
                            // Afficher aussi le bouton standard
                            downloadButton.style.display = 'inline-block';
                        }
                    }
                })
                .catch(error => {
                    console.error("Erreur lors de la vérification du PDF:", error);
                    
                    if (attempts < maxAttempts) {
                        // En cas d'erreur, on continue d'essayer
                        setTimeout(checkStatus, 3000);
                    } else {
                        // Après toutes les tentatives, on donne une option pour télécharger quand même
                        commandOutput.innerHTML = `
                            <div class="command-header" style="color: #3b82f6">Traitement terminé</div>
                            <p>Le PDF a peut-être été généré malgré les erreurs. Vous pouvez tenter de le télécharger.</p>
                            <button id="try-download-button" class="download-button">Tenter le téléchargement</button>
                        `;
                        
                        document.getElementById('try-download-button').addEventListener('click', function() {
                            downloadLatestPDF();
                        });
                        
                        // Afficher aussi le bouton standard
                        downloadButton.style.display = 'inline-block';
                    }
                });
            })
            .catch(error => {
                // Erreur lors de la vérification, on continue avec la méthode HEAD
                fetch(`/client/${clientId}/download_pdf`, {
                    method: 'HEAD',
                    credentials: 'include'
                })
                .then(response => {
                    if (response.ok) {
                        downloadButton.style.display = 'inline-block';
                        commandOutput.innerHTML = `
                            <div class="command-header" style="color: #10b981">PDF généré avec succès</div>
                            <p>Le rapport PDF a été généré et est prêt à être téléchargé.</p>
                        `;
                    } else if (attempts < maxAttempts) {
                        setTimeout(checkStatus, 3000);
                    } else {
                        // Afficher quand même le bouton après le nombre maximum de tentatives
                        downloadButton.style.display = 'inline-block';
                        commandOutput.innerHTML = `
                            <div class="command-header" style="color: #3b82f6">Traitement terminé</div>
                            <p>Le PDF a peut-être été généré malgré les erreurs. Vous pouvez tenter de le télécharger.</p>
                        `;
                    }
                })
                .catch(() => {
                    if (attempts < maxAttempts) {
                        setTimeout(checkStatus, 3000);
                    } else {
                        // Afficher quand même le bouton après le nombre maximum de tentatives
                        downloadButton.style.display = 'inline-block';
                        commandOutput.innerHTML = `
                            <div class="command-header" style="color: #3b82f6">Traitement terminé</div>
                            <p>Le PDF a peut-être été généré malgré les erreurs. Vous pouvez tenter de le télécharger.</p>
                        `;
                    }
                });
            });
        };
        
        // Commencer à vérifier
        checkStatus();
    }
});

function openClientSettings(clientId) {
    window.location.href = `settings.html?client_id=${clientId}`;
}

// Adapter la fonction qui affiche les clients pour inclure un bouton Settings
function displayClients(clients) {
    const clientList = document.getElementById('clientList');
    clientList.innerHTML = '';
    
    clients.forEach(client => {
        // Autres éléments d'affichage existants...
        
        // Ajouter un bouton Settings
        const settingsButton = document.createElement('button');
        settingsButton.className = 'btn btn-info btn-sm';
        settingsButton.innerHTML = '<i class="material-icons">settings</i> Paramètres';
        settingsButton.onclick = function() {
            openClientSettings(client.id);
        };
        
        // Ajouter le bouton au conteneur des actions du client
        const actionsContainer = document.getElementById(`client-actions-${client.id}`);
        actionsContainer.appendChild(settingsButton);
    });
}

// Fonction pour appliquer les états visuels en fonction des paramètres activés/désactivés
function applyFeatureVisibility(settings) {
    // Système de ressources
    const resourcesArea = document.querySelector('.resources-area');
    toggleSectionVisibility(resourcesArea, settings.system_resources_enabled, "Surveillance des ressources désactivée");
    
    // Logs d'activité
    const logsArea = document.querySelector('.logs-area');
    toggleSectionVisibility(logsArea, settings.activity_logs_enabled, "Journalisation des activités désactivée");
    
    // Détection de fichiers suspects
    const malwareScanArea = document.querySelector('.malware-scan-area');
    toggleSectionVisibility(malwareScanArea, settings.file_detection_enabled, "Détection de fichiers suspects désactivée");
    
    // Si VirusTotal est désactivé mais la détection de fichiers est activée, afficher un message
    if (!settings.virustotal_enabled && settings.file_detection_enabled && malwareScanArea) {
        const vtWarning = document.createElement('div');
        vtWarning.className = 'alert alert-warning';
        vtWarning.textContent = 'L\'analyse VirusTotal est désactivée. Les fichiers suspects sont détectés mais pas analysés.';
        malwareScanArea.prepend(vtWarning);
    }
    
    // Afficher un résumé des fonctionnalités actives
    updateFeatureIndicators(settings);
}

function toggleSectionVisibility(element, isEnabled, disabledMessage) {
    if (!element) return;
    
    if (isEnabled) {
        element.classList.remove('disabled-section');
        // Supprimer l'icône si elle existe
        const existingIcon = element.querySelector('.disabled-icon');
        if (existingIcon) {
            element.removeChild(existingIcon);
        }
    } else {
        element.classList.add('disabled-section');
        
        // S'assurer qu'on n'ajoute pas plusieurs icônes
        if (!element.querySelector('.disabled-icon')) {
            const disabledIcon = document.createElement('div');
            disabledIcon.className = 'disabled-icon';
            disabledIcon.textContent = '✕';
            disabledIcon.title = disabledMessage;
            element.appendChild(disabledIcon);
        }
    }
}

function updateFeatureIndicators(settings) {
    const devicePage = document.getElementById('device-page');
    if (!devicePage) return;
    
    // Vérifier si le conteneur d'indicateurs existe déjà, sinon le créer
    let indicatorsContainer = devicePage.querySelector('.feature-indicators');
    if (!indicatorsContainer) {
        indicatorsContainer = document.createElement('div');
        indicatorsContainer.className = 'feature-indicators';
        
        // Insérer après le titre de l'appareil
        const deviceTitle = devicePage.querySelector('h2');
        if (deviceTitle && deviceTitle.nextSibling) {
            devicePage.insertBefore(indicatorsContainer, deviceTitle.nextSibling);
        } else {
            devicePage.prepend(indicatorsContainer);
        }
    } else {
        // Vider le conteneur existant
        indicatorsContainer.innerHTML = '';
    }
    
    // Créer les indicateurs de fonctionnalités
    const features = [
        { name: 'Ressources système', enabled: settings.system_resources_enabled },
        { name: 'Journaux d\'activité', enabled: settings.activity_logs_enabled },
        { name: 'Détection de fichiers', enabled: settings.file_detection_enabled },
        { name: 'Analyse VirusTotal', enabled: settings.virustotal_enabled }
    ];
    
    features.forEach(feature => {
        const indicator = document.createElement('div');
        indicator.className = `feature-indicator ${feature.enabled ? 'feature-enabled' : 'feature-disabled'}`;
        indicator.innerHTML = `<i>${feature.enabled ? '✓' : '✕'}</i> ${feature.name}`;
        indicatorsContainer.appendChild(indicator);
    });
}

// Pour s'assurer que les états visuels sont appliqués aussi lors du chargement initial de la page
// si un client est déjà sélectionné (depuis localStorage par exemple)
document.addEventListener('DOMContentLoaded', function() {
    // Vérifier si un client était précédemment sélectionné
    const savedClientId = localStorage.getItem('currentClientId');
    const savedClientName = localStorage.getItem('currentClientName');
    
    if (savedClientId && savedClientName) {
        showDevicePage(savedClientId, savedClientName);
    }
});

// Fonction pour réinitialiser la base de données
function resetDatabase() {
    showCustomDialog(
        "Êtes-vous sûr de vouloir réinitialiser la base de données? Cette action est irréversible et supprimera toutes les données.",
        () => {
            // L'utilisateur a confirmé, procéder à la réinitialisation
            fetch('/reset_database', {
                method: 'POST',
                credentials: 'include'
            })
            .then(response => response.json())
            .then(data => {
                alert(data.message);
                // Recharger la page après réinitialisation
                window.location.reload();
            })
            .catch(error => {
                console.error('Erreur:', error);
                alert('Erreur lors de la réinitialisation: ' + error);
            });
        },
        null,
        true
    );
}

// Ajouter un event listener au bouton de reset DB
document.addEventListener('DOMContentLoaded', function() {
    const resetBtn = document.getElementById('resetDB');
    if (resetBtn) {
        resetBtn.addEventListener('click', resetDatabase);
    }
});

const filterCheckboxes = document.querySelectorAll('.logs-filter input[type="checkbox"]');
filterCheckboxes.forEach(checkbox => {
    checkbox.addEventListener('change', applyLogFilters);
});

function getLogTypeClass(type) {
    return type.toLowerCase()
        .replace('é', 'e')
        .replace('è', 'e')
        .replace('ê', 'e')
        .replace('à', 'a')
        .replace('ç', 'c');
}

function applyLogFilters() {
    const logEntries = document.querySelectorAll('.log-entry');
    const showFile = document.getElementById('filter-file').checked;
    const showFolder = document.getElementById('filter-folder').checked;
    const showExe = document.getElementById('filter-exe').checked;
    const showCreated = document.getElementById('filter-created').checked;
    const showModified = document.getElementById('filter-modified').checked;
    const showDeleted = document.getElementById('filter-deleted').checked;
    const showMoved = document.getElementById('filter-moved').checked;

    logEntries.forEach(entry => {
        const elementType = entry.getAttribute('data-element-type');
        const logType = entry.getAttribute('data-log-type');
        let showEntry = true;
        if (elementType === 'file' && !showFile) showEntry = false;
        if (elementType === 'folder' && !showFolder) showEntry = false;
        if (elementType === 'exe' && !showExe) showEntry = false;
        if (logType === 'Création' && !showCreated) showEntry = false;
        if (logType === 'Modification' && !showModified) showEntry = false;
        if (logType === 'Suppression' && !showDeleted) showEntry = false;
        if (logType === 'Déplacement' && !showMoved) showEntry = false;
        entry.style.display = showEntry ? 'block' : 'none';
    });
}

// Re-ajouter la fonction de dialogue personnalisé qui a été supprimée
function showCustomDialog(message, onConfirm = null, onCancel = null, isConfirm = false) {
    // Créer l'élément de dialogue
    const dialogEl = document.createElement('div');
    dialogEl.className = 'custom-dialog';
    
    // Contenu du dialogue
    let dialogContent = `
        <div class="dialog-content">
            <div class="dialog-message">${message}</div>
            <div class="dialog-buttons">
    `;
    
    // Ajouter les boutons selon le type (confirm ou alert)
    if (isConfirm) {
        dialogContent += `
                <button class="dialog-button dialog-button-confirm" id="dialog-confirm-btn">Confirmer</button>
                <button class="dialog-button dialog-button-cancel" id="dialog-cancel-btn">Annuler</button>
        `;
    } else {
        dialogContent += `
                <button class="dialog-button dialog-button-confirm" id="dialog-ok-btn">OK</button>
        `;
    }
    
    dialogContent += `
            </div>
        </div>
    `;
    
    dialogEl.innerHTML = dialogContent;
    document.body.appendChild(dialogEl);
    
    // Ajouter les gestionnaires d'événements
    if (isConfirm) {
        const confirmBtn = document.getElementById('dialog-confirm-btn');
        const cancelBtn = document.getElementById('dialog-cancel-btn');
        
        confirmBtn.addEventListener('click', function() {
            if (onConfirm) onConfirm();
            document.body.removeChild(dialogEl);
        });
        
        cancelBtn.addEventListener('click', function() {
            if (onCancel) onCancel();
            document.body.removeChild(dialogEl);
        });
    } else {
        const okBtn = document.getElementById('dialog-ok-btn');
        
        okBtn.addEventListener('click', function() {
            if (onConfirm) onConfirm();
            document.body.removeChild(dialogEl);
        });
    }
}

// Ajouter un gestionnaire pour le bouton API qui a été supprimé
document.addEventListener('DOMContentLoaded', function() {
    const executeAPIbutton = document.getElementById('execute-api-button');
    if (executeAPIbutton) {
        executeAPIbutton.addEventListener('click', function() {
            const token = document.getElementById('api-input').value;
            if (!token || !window.currentClientId) return;
            
            const commandOutput = document.getElementById('api-output');
            commandOutput.style.display = 'block';
            commandOutput.innerHTML = `<div class="command-spinner"></div>Envoi...`;
            
            fetch(`/client/${window.currentClientId}/token`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ token: token }),
                credentials: 'include'
            })
            .then(response => response.json())
            .then(data => {
                commandOutput.innerHTML = 'API mise à jour';
            })
            .catch(error => {
                commandOutput.innerHTML = 'Erreur: ' + error.message;
            });
        });
    }

    // Initialiser les boutons au chargement de la page
    initializeButtons();
});