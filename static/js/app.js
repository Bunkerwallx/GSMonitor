class GSMMonitorApp {
    constructor() {
        this.socket = io();
        this.isMonitoring = false;
        this.setupEventListeners();
        this.setupSocketListeners();
    }

    setupEventListeners() {
        // Formulario de monitoreo
        document.getElementById('monitoring-form').addEventListener('submit', (e) => {
            e.preventDefault();
            this.startMonitoring();
        });

        // Botón de detener
        document.getElementById('stop-btn').addEventListener('click', () => {
            this.stopMonitoring();
        });

        // Botones de exportación
        document.getElementById('export-json').addEventListener('click', () => {
            this.exportData('json');
        });

        document.getElementById('export-csv').addEventListener('click', () => {
            this.exportData('csv');
        });
    }

    setupSocketListeners() {
        this.socket.on('connect', () => {
            this.updateStatusIndicator('connected', 'Conectado');
        });

        this.socket.on('disconnect', () => {
            this.updateStatusIndicator('disconnected', 'Desconectado');
        });

        this.socket.on('monitoring_update', (data) => {
            this.updateProgress(data);
        });

        this.socket.on('monitoring_complete', (data) => {
            this.monitoringComplete(data);
        });

        this.socket.on('monitoring_error', (data) => {
            this.showError(data.error);
        });
    }

    async startMonitoring() {
        const formData = {
            phone_number: document.getElementById('phone_number').value,
            operator: document.getElementById('operator').value,
            duration: document.getElementById('duration').value,
            visualization: document.getElementById('visualization').value
        };

        try {
            const response = await fetch('/start_monitoring', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(formData)
            });

            const result = await response.json();

            if (result.status === 'success') {
                this.isMonitoring = true;
                this.updateUIForMonitoring(true);
                this.showToast('Monitoreo iniciado correctamente', 'success');
            } else {
                this.showError(result.message);
            }
        } catch (error) {
            this.showError('Error de conexión: ' + error.message);
        }
    }

    async stopMonitoring() {
        try {
            const response = await fetch('/stop_monitoring', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
            });

            const result = await response.json();

            if (result.status === 'success') {
                this.isMonitoring = false;
                this.updateUIForMonitoring(false);
                this.showToast('Monitoreo detenido', 'warning');
            }
        } catch (error) {
            this.showError('Error deteniendo monitoreo: ' + error.message);
        }
    }

    updateUIForMonitoring(monitoring) {
        const startBtn = document.getElementById('start-btn');
        const stopBtn = document.getElementById('stop-btn');
        const progressPanel = document.getElementById('progress-panel');
        const resultsPanel = document.getElementById('results-panel');

        startBtn.disabled = monitoring;
        stopBtn.disabled = !monitoring;

        if (monitoring) {
            progressPanel.style.display = 'block';
            resultsPanel.style.display = 'block';
            startBtn.classList.remove('btn-success');
            startBtn.classList.add('btn-secondary');
        } else {
            progressPanel.style.display = 'none';
            startBtn.classList.remove('btn-secondary');
            startBtn.classList.add('btn-success');
        }
    }

    updateProgress(data) {
        // Actualizar barra de progreso
        const progressBar = document.getElementById('progress-bar');
        const progressText = document.getElementById('progress-text');
        const currentOp = document.getElementById('current-operation');

        progressBar.style.width = `${data.progress}%`;
        progressText.textContent = `${Math.round(data.progress)}%`;
        currentOp.textContent = data.current_operation;

        // Actualizar contadores
        document.getElementById('imsi-count').textContent = data.detected_imsis;
        document.getElementById('location-count').textContent = data.locations;
        document.getElementById('packet-count').textContent = data.packets_analyzed || 0;
        document.getElementById('cell-count').textContent = data.unique_cells || 0;

        // Actualizar tabla de resultados
        this.updateResultsTable(data);
    }

    updateResultsTable(data) {
        // En una implementación real, aquí actualizarías la tabla con los resultados
        const tableBody = document.getElementById('results-table');
        
        // Simulación de actualización de tabla
        if (data.locations > 0) {
            tableBody.innerHTML = `
                <tr>
                    <td>334020123456789</td>
                    <td>19.4326, -99.1332</td>
                    <td><span class="badge bg-success">1.2 km</span></td>
                    <td>${new Date().toLocaleTimeString()}</td>
                </tr>
            `;
        }
    }

    monitoringComplete(data) {
        this.isMonitoring = false;
        this.updateUIForMonitoring(false);
        
        this.showToast('Monitoreo completado', 'success');
        console.log('Resultados finales:', data);
    }

    async exportData(format) {
        try {
            const response = await fetch(`/export/${format}`);
            if (response.ok) {
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.style.display = 'none';
                a.href = url;
                a.download = `gsm_monitor_export.${format}`;
                document.body.appendChild(a);
                a.click();
                window.URL.revokeObjectURL(url);
                this.showToast(`Datos exportados en formato ${format.toUpperCase()}`, 'success');
            } else {
                const error = await response.json();
                this.showError(error.message);
            }
        } catch (error) {
            this.showError('Error exportando datos: ' + error.message);
        }
    }

    updateStatusIndicator(status, text) {
        const indicator = document.getElementById('status-indicator');
        indicator.textContent = text;
        indicator.className = `badge bg-${status === 'connected' ? 'success' : 'danger'}`;
    }

    showToast(message, type = 'info') {
        // Implementación simple de toast
        const toast = document.createElement('div');
        toast.className = `alert alert-${type} alert-dismissible fade show`;
        toast.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        document.querySelector('main').prepend(toast);
        
        // Auto-remover después de 5 segundos
        setTimeout(() => {
            toast.remove();
        }, 5000);
    }

    showError(message) {
        this.showToast(message, 'danger');
    }
}

// Inicializar la aplicación cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', () => {
    new GSMMonitorApp();
});
