// EVE Local Threat Monitor Dashboard JavaScript

class ThreatDashboard {
    constructor() {
        this.apiUrl = '/api/threats';
        this.statusUrl = '/api/status';
        this.refreshInterval = 2000; // 2 seconds
        this.statusCheckInterval = 1000; // 1 second
        this.lastUpdateTime = null;
        this.monitorRunning = true;
        this.init();
    }

    init() {
        console.log('Initializing EVE Local Threat Monitor Dashboard');
        this.setupControlButtons();
        this.startAutoRefresh();
        this.startStatusCheck();
    }

    setupControlButtons() {
        document.getElementById('start-stop-btn').addEventListener('click', () => {
            this.toggleMonitor();
        });

        document.getElementById('restart-btn').addEventListener('click', () => {
            this.restartMonitor();
        });

        document.getElementById('reconfig-btn').addEventListener('click', () => {
            this.reconfigureOCR();
        });

        document.getElementById('exit-btn').addEventListener('click', () => {
            this.exitApplication();
        });
    }

    async toggleMonitor() {
        if (this.monitorRunning) {
            // Stop the monitor
            if (!confirm('Stop the monitor? (Web dashboard will stay running)')) {
                return;
            }

            try {
                const response = await fetch('/api/stop', { method: 'POST' });
                if (response.ok) {
                    console.log('Monitor stopped.');
                } else {
                    alert('Failed to stop monitor. Check the console for errors.');
                }
            } catch (error) {
                console.error('Error stopping monitor:', error);
                alert('Error communicating with monitor.');
            }
        } else {
            // Start the monitor
            try {
                const response = await fetch('/api/start', { method: 'POST' });
                if (response.ok) {
                    console.log('Monitor starting...');
                } else {
                    alert('Failed to start monitor. Check the console for errors.');
                }
            } catch (error) {
                console.error('Error starting monitor:', error);
                alert('Error communicating with monitor.');
            }
        }
    }

    async restartMonitor() {
        if (!confirm('Restart the monitor? (Clears cache and restarts scanning)')) {
            return;
        }

        try {
            const response = await fetch('/api/restart', { method: 'POST' });
            if (response.ok) {
                console.log('Monitor restarting...');
            } else {
                alert('Failed to restart monitor. Check the console for errors.');
            }
        } catch (error) {
            console.error('Error restarting monitor:', error);
            alert('Error communicating with monitor.');
        }
    }

    async exitApplication() {
        if (!confirm('Exit the entire application? (Monitor and web server will stop)')) {
            return;
        }

        try {
            const response = await fetch('/api/exit', { method: 'POST' });
            if (response.ok) {
                alert('Application shutting down. This page will become unavailable.');
            } else {
                alert('Failed to exit application. Check the console for errors.');
            }
        } catch (error) {
            console.error('Error exiting application:', error);
            alert('Error communicating with monitor.');
        }
    }

    async checkMonitorStatus() {
        try {
            const response = await fetch(this.statusUrl);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const data = await response.json();
            this.updateMonitorStatus(data.monitor_running);
        } catch (error) {
            console.error('Error checking monitor status:', error);
        }
    }

    updateMonitorStatus(isRunning) {
        this.monitorRunning = isRunning;
        const statusIndicator = document.getElementById('monitor-status');
        const statusText = document.getElementById('monitor-status-text');
        const startStopBtn = document.getElementById('start-stop-btn');

        if (isRunning) {
            statusIndicator.className = 'status-indicator running';
            statusText.textContent = 'Running';
            startStopBtn.textContent = 'Stop Monitor';
            startStopBtn.className = 'control-btn warning';
        } else {
            statusIndicator.className = 'status-indicator stopped';
            statusText.textContent = 'Stopped';
            startStopBtn.textContent = 'Start Monitor';
            startStopBtn.className = 'control-btn info';
        }
    }

    startStatusCheck() {
        // Initial check
        this.checkMonitorStatus();

        // Set up periodic status check
        setInterval(() => {
            this.checkMonitorStatus();
        }, this.statusCheckInterval);
    }

    async reconfigureOCR() {
        if (!confirm('This will launch the region selector. Make sure you can see your EVE Local window.')) {
            return;
        }

        try {
            const response = await fetch('/api/reconfigure', { method: 'POST' });
            if (response.ok) {
                alert('Region selector will launch. Select your Local window area and the monitor will restart automatically.');
            } else {
                alert('Failed to launch region selector. Check the console for errors.');
            }
        } catch (error) {
            console.error('Error launching region selector:', error);
            alert('Error communicating with monitor.');
        }
    }

    async fetchThreats() {
        try {
            const response = await fetch(this.apiUrl);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const data = await response.json();
            this.updateUI(data);
            this.updateConnectionStatus(true);
        } catch (error) {
            console.error('Error fetching threats:', error);
            this.updateConnectionStatus(false);
        }
    }

    updateUI(data) {
        // Update player count
        document.getElementById('player-count').textContent = data.player_count || 0;

        // Update last update time
        if (data.last_update) {
            const updateTime = new Date(data.last_update * 1000);
            document.getElementById('last-update').textContent = this.formatTime(updateTime);
        }

        // Update threats list
        const threatsContainer = document.getElementById('threats-list');
        const noDataContainer = document.getElementById('no-data');

        if (data.threats && data.threats.length > 0) {
            noDataContainer.style.display = 'none';
            threatsContainer.style.display = 'block';
            this.renderThreats(data.threats);
        } else {
            noDataContainer.style.display = 'block';
            threatsContainer.style.display = 'none';
        }
    }

    renderThreats(threats) {
        const container = document.getElementById('threats-list');

        container.innerHTML = threats.map(threat => {
            // Use danger_ratio from backend
            const dangerRatio = threat.danger_ratio || 0;
            const dangerLevel = this.getDangerLevel(dangerRatio);
            const indicator = this.getDangerIndicator(dangerRatio);

            return `
                <div class="threat-item danger-${dangerLevel}">
                    <div class="threat-header">
                        <div class="threat-name">${this.escapeHtml(threat.name || 'Unknown')}</div>
                        <div class="threat-indicator">${indicator}</div>
                    </div>
                    <div class="threat-details">
                        <div class="detail-item">
                            <span class="detail-label">Corporation</span>
                            <span class="detail-value">${this.escapeHtml(threat.corporation || 'Unknown')}</span>
                        </div>
                        <div class="detail-item">
                            <span class="detail-label">Alliance</span>
                            <span class="detail-value">${this.escapeHtml(threat.alliance || 'None')}</span>
                        </div>
                        <div class="detail-item">
                            <span class="detail-label">Danger Rating</span>
                            <span class="detail-value danger-percent ${dangerLevel}">${Math.round(dangerRatio)}%</span>
                        </div>
                        <div class="detail-item">
                            <span class="detail-label">Kills / Deaths</span>
                            <span class="detail-value">${threat.kills || 0} / ${threat.losses || 0}</span>
                        </div>
                        <div class="detail-item">
                            <span class="detail-label">Top Ships</span>
                            <span class="detail-value ships-list">${this.formatShips(threat.top_ships)}</span>
                        </div>
                    </div>
                </div>
            `;
        }).join('');
    }

    getDangerLevel(dangerPercent) {
        if (dangerPercent === null || dangerPercent === undefined) return 'unknown';
        if (dangerPercent >= 70) return 'high';
        if (dangerPercent >= 40) return 'medium';
        if (dangerPercent > 0) return 'low';
        return 'unknown';
    }

    getDangerIndicator(dangerPercent) {
        if (dangerPercent === null || dangerPercent === undefined) return '⚪';
        if (dangerPercent >= 70) return '🔴';
        if (dangerPercent >= 40) return '🟡';
        return '🟢';
    }

    formatShips(ships) {
        if (!ships || ships.length === 0) return 'Unknown';
        return ships.slice(0, 3).map(ship => ship.ship_name).join(', ');
    }

    formatTime(date) {
        const now = new Date();
        const diffSeconds = Math.floor((now - date) / 1000);

        if (diffSeconds < 5) return 'Just now';
        if (diffSeconds < 60) return `${diffSeconds}s ago`;
        if (diffSeconds < 3600) return `${Math.floor(diffSeconds / 60)}m ago`;

        return date.toLocaleTimeString();
    }

    updateConnectionStatus(isOnline) {
        const indicator = document.getElementById('connection-status');
        if (isOnline) {
            indicator.className = 'status-indicator online';
        } else {
            indicator.className = 'status-indicator offline';
        }
    }

    escapeHtml(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    startAutoRefresh() {
        // Initial fetch
        this.fetchThreats();

        // Set up auto-refresh
        setInterval(() => {
            this.fetchThreats();
        }, this.refreshInterval);
    }
}

// Initialize dashboard when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    new ThreatDashboard();
});
