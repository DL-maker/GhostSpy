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

    let currentClientId = null;
    let screenshotPollingInterval;
    let resourcePollingInterval;
    let logsPollingInterval;
    let scanResultsPollingInterval;
    let lastProcessedLogTime = null;

    function fetchClients() {
        fetch('/clients')
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
                });
                connectedCountSpan.textContent = connectedClients;
                disconnectedCountSpan.textContent = disconnectedClients;
            })
            .catch(error => console.error('Error fetching clients:', error));
    }

    window.showDevicePage = function(clientId, clientName) {
        currentClientId = clientId;
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
        lastProcessedLogTime = null;
    }

    window.disconnectClient = function(clientId) {
        fetch(`/client/${clientId}/disconnect`, {
            method: 'POST',
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

    executeCommandButton.addEventListener('click', function() {
        const command = commandInput.value;
        if (command && currentClientId) {
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
                setTimeout(() => {
                    checkCommandResult(currentClientId);
                }, 2000);
                commandInput.value = '';
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
                let resultHtml = `
                    <div class="command-header">
                        Commande : <span style="color: #38bdf8">${data.output.command}</span>
                    </div>`;

                if (data.output.stdout && data.output.stdout.trim() !== '') {
                    resultHtml += `
                        <div>
                            <div style="color: #94a3b8; margin-top: 10px;">STDOUT :</div>
                            <pre class="command-stdout">${escapeHtml(data.output.stdout)}</pre>
                        </div>`;
                } else {
                    resultHtml += `<div style="color: #94a3b8; margin-top: 10px;">STDOUT : (Pas de sortie)</div>`;
                }

                if (data.output.stderr && data.output.stderr.trim() !== '') {
                    resultHtml += `
                        <div>
                            <div style="color: #94a3b8; margin-top: 10px;">STDERR :</div>
                            <pre class="command-stderr">${escapeHtml(data.output.stderr)}</pre>
                        </div>`;
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

    function escapeHtml(unsafe) {
        return unsafe
             .replace(/&/g, "&amp;")
             .replace(/</g, "&lt;")
             .replace(/>/g, "&gt;")
             .replace(/"/g, "&quot;")
             .replace(/'/g, "&#039;");
    }

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
        fetch(`/client/${clientId}/logs`)
        .then(response => response.json())
        .then(data => {
            if (data.logs && data.logs.length > 0) {
                displayLogs(data.logs);
            }
        })
        .catch(error => console.error('Erreur lors de la récupération des logs:', error));
    }

    function displayLogs(logs) {
        const logsContainer = document.getElementById('logs-container');
        logs.sort((a, b) => a.time.localeCompare(b.time));
        if (!lastProcessedLogTime) {
            logsContainer.innerHTML = "";
        }
        const newLogs = logs.filter(log => !lastProcessedLogTime || log.time > lastProcessedLogTime);
        if (newLogs.length > 0) {
            lastProcessedLogTime = logs[logs.length - 1].time;
            newLogs.forEach(log => {
                const logElement = createLogElement(log);
                logsContainer.appendChild(logElement);
            });
            logsContainer.scrollTop = logsContainer.scrollHeight;
        }
    }

    function createLogElement(log) {
        const logEntry = document.createElement('div');
        const elementClass = `log-entry log-entry-${log.element_type}`;
        logEntry.className = log.warning ? elementClass + ' log-entry-warning' : elementClass;
        logEntry.setAttribute('data-element-type', log.element_type);
        logEntry.setAttribute('data-log-type', log.type);

        let logContent = `
            <span class="log-time">[${log.time}]</span>
            <span class="log-type log-type-${getLogTypeClass(log.type)}">${log.type}</span>
            <span class="log-name">${escapeHtml(log.name)}</span>
            <div class="log-path">${escapeHtml(log.path)}</div>
        `;
        if (log.warning) {
            logContent += `<div class="log-warning">${escapeHtml(log.warning)}</div>`;
        }
        if (log.dest_path) {
            logContent += `<div class="log-path">→ ${escapeHtml(log.dest_path)}</div>`;
        }
        logEntry.innerHTML = logContent;
        return logEntry;
    }

    function getLogTypeClass(type) {
        return type.toLowerCase()
            .replace('é', 'e')
            .replace('è', 'e')
            .replace('ê', 'e')
            .replace('à', 'a')
            .replace('ç', 'c');
    }

    const filterCheckboxes = document.querySelectorAll('.logs-filter input[type="checkbox"]');
    filterCheckboxes.forEach(checkbox => {
        checkbox.addEventListener('change', applyLogFilters);
    });

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

    function fetchScanResults(clientId) {
        fetch(`/client/${clientId}/scan_file`)
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
});