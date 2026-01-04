// EVE Local Threat Monitor Dashboard JavaScript

class ThreatDashboard {
    constructor() {
        this.apiUrl = '/api/threats';
        this.refreshInterval = 2000; // 2 seconds
        this.lastUpdateTime = null;
        this.init();
    }

    init() {
        console.log('Initializing EVE Local Threat Monitor Dashboard');
        this.setupControlButtons();
        this.startAutoRefresh();
    }

    setupControlButtons() {
        document.getElementById('shutdown-btn').addEventListener('click', () => {
            this.shutdownMonitor();
        });

        document.getElementById('restart-btn').addEventListener('click', () => {
            this.restartMonitor();
        });

        document.getElementById('reconfig-btn').addEventListener('click', () => {
            this.reconfigureOCR();
        });
    }

    async shutdownMonitor() {
        if (!confirm('Are you sure you want to shutdown the monitor?')) {
            return;
        }

        try {
            const response = await fetch('/api/shutdown', { method: 'POST' });
            if (response.ok) {
                alert('Monitor shutdown initiated. The web server will stop shortly.');
            } else {
                alert('Failed to shutdown monitor. Check the console for errors.');
            }
        } catch (error) {
            console.error('Error shutting down monitor:', error);
            alert('Error communicating with monitor.');
        }
    }

    async restartMonitor() {
        if (!confirm('Are you sure you want to restart the monitor?')) {
            return;
        }

        try {
            const response = await fetch('/api/restart', { method: 'POST' });
            if (response.ok) {
                alert('Monitor restart initiated.');
            } else {
                alert('Failed to restart monitor. Check the console for errors.');
            }
        } catch (error) {
            console.error('Error restarting monitor:', error);
            alert('Error communicating with monitor.');
        }
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
