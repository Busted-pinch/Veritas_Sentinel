const API_BASE = 'http://localhost:8000';

// Auth check
const token = localStorage.getItem('token');
const user = JSON.parse(localStorage.getItem('user') || '{}');

if (!token || user.role !== 'admin') {
    window.location.href = 'login.html';
}

// API Helper
async function apiCall(endpoint, options = {}) {
    const response = await fetch(`${API_BASE}${endpoint}`, {
        ...options,
        headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
            ...options.headers
        }
    });

    if (response.status === 401) {
        localStorage.clear();
        window.location.href = 'login.html';
        throw new Error('Unauthorized');
    }

    return response.json();
}

// Global state
let currentPage = 'overview';
let charts = {};
let geoMap = null;
let currentAlertId = null;

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    initializePage();
    setupEventListeners();
    loadInitialData();
});

function initializePage() {
    // Set user info
    document.getElementById('userName').textContent = user.email?.split('@')[0] || 'Admin';
    document.getElementById('userInitials').textContent = (user.email?.[0] || 'A').toUpperCase();
}

function setupEventListeners() {
    // Navigation
    document.querySelectorAll('.nav-item').forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();
            const page = item.dataset.page;
            navigateToPage(page);
        });
    });

    // Menu toggle
    document.getElementById('menuBtn')?.addEventListener('click', () => {
        document.getElementById('sidebar').classList.toggle('show');
    });

    // Logout
    document.getElementById('logoutBtn').addEventListener('click', () => {
        localStorage.clear();
        window.location.href = 'login.html';
    });

    // Refresh
    document.getElementById('refreshBtn').addEventListener('click', () => {
        loadPageData(currentPage);
    });

    // User search
    document.getElementById('userSearch')?.addEventListener('input', debounce(searchUsers, 500));

    // Alert filter
    document.getElementById('alertFilter')?.addEventListener('change', loadAlerts);

    // Geo time range
    document.getElementById('geoTimeRange')?.addEventListener('change', loadGeoHotspots);

    // Intelligence search
    document.getElementById('searchIntelBtn')?.addEventListener('click', searchIntelligence);

    // Modal
    document.getElementById('closeModal')?.addEventListener('click', closeModal);
    document.getElementById('cancelResolve')?.addEventListener('click', closeModal);
    document.getElementById('confirmResolve')?.addEventListener('click', confirmResolveAlert);
     // Create user form
    document.getElementById('createUserForm')?.addEventListener('submit', handleCreateUser);
    document.getElementById('resetCreateUser')?.addEventListener('click', () => {
        document.getElementById('createUserForm').reset();
    });

}

function navigateToPage(page) {
    currentPage = page;
    
    // Update nav
    document.querySelectorAll('.nav-item').forEach(item => {
        item.classList.toggle('active', item.dataset.page === page);
    });

    // Update page content
    document.querySelectorAll('.page-content').forEach(content => {
        content.classList.toggle('active', content.id === `${page}Page`);
    });

    // Update title
    const titles = {
        overview: 'Overview',
        users: 'Users',
        analytics: 'Analytics',
        alerts: 'Alerts',
        intelligence: 'Intelligence'
    };
    document.getElementById('pageTitle').textContent = titles[page] || page;

    // Load page data
    loadPageData(page);
}

async function loadInitialData() {
    loadPageData('overview');
}

async function loadPageData(page) {
    switch(page) {
        case 'overview':
            await loadOverview();
            break;
        case 'users':
            await loadUsers();
            break;
        case 'analytics':
            await loadAnalytics();
            break;
        case 'alerts':
            await loadAlerts();
            break;
    }
}

// ===== OVERVIEW PAGE =====
async function loadOverview() {
    try {
        // Load users count
        const users = await apiCall('/api/admin/users?limit=1000');
        document.getElementById('totalUsers').textContent = users.length;

        // Load alerts
        const alerts = await apiCall('/api/admin/alerts');
        const openAlerts = alerts.filter(a => a.status === 'open');
        document.getElementById('openAlerts').textContent = openAlerts.length;
        document.getElementById('alertsBadge').textContent = openAlerts.length;

        // Load global risk trend
        const riskData = await apiCall('/api/admin/risk-trend-global?days=30');
        
        if (riskData.success && riskData.days.length > 0) {
            const today = riskData.days[riskData.days.length - 1];
            document.getElementById('txnsToday').textContent = today.total_txns;
            document.getElementById('avgRisk').textContent = today.avg_risk.toFixed(1);

            // Render risk trend chart
            renderRiskTrendChart(riskData.days);

            // Calculate risk distribution
            const distribution = calculateRiskDistribution(riskData.days);
            renderRiskDistributionChart(distribution);
        } else {
            document.getElementById('txnsToday').textContent = '0';
            document.getElementById('avgRisk').textContent = '0';
        }
    } catch (error) {
        console.error('Error loading overview:', error);
    }
}

function calculateRiskDistribution(days) {
    const distribution = { low: 0, medium: 0, high: 0, critical: 0 };
    
    days.forEach(day => {
        if (day.avg_risk < 40) distribution.low++;
        else if (day.avg_risk < 65) distribution.medium++;
        else if (day.avg_risk < 85) distribution.high++;
        else distribution.critical++;
    });
    
    return distribution;
}

function renderRiskTrendChart(days) {
    const ctx = document.getElementById('riskTrendChart');
    
    if (charts.riskTrend) {
        charts.riskTrend.destroy();
    }

    charts.riskTrend = new Chart(ctx, {
        type: 'line',
        data: {
            labels: days.map(d => d.date),
            datasets: [{
                label: 'Avg Risk Score',
                data: days.map(d => d.avg_risk),
                borderColor: 'rgb(239, 68, 68)',
                backgroundColor: 'rgba(239, 68, 68, 0.1)',
                tension: 0.4,
                fill: true
            }, {
                label: 'Avg Fraud Probability',
                data: days.map(d => d.avg_fraud_probability),
                borderColor: 'rgb(245, 158, 11)',
                backgroundColor: 'rgba(245, 158, 11, 0.1)',
                tension: 0.4,
                fill: true
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: true,
                    position: 'top'
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    max: 100
                }
            }
        }
    });
}

function renderRiskDistributionChart(distribution) {
    const ctx = document.getElementById('riskDistributionChart');
    
    if (charts.riskDistribution) {
        charts.riskDistribution.destroy();
    }

    charts.riskDistribution = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['Low', 'Medium', 'High', 'Critical'],
            datasets: [{
                data: [distribution.low, distribution.medium, distribution.high, distribution.critical],
                backgroundColor: [
                    'rgb(59, 130, 246)',
                    'rgb(245, 158, 11)',
                    'rgb(249, 115, 22)',
                    'rgb(239, 68, 68)'
                ]
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom'
                }
            }
        }
    });
}

// ===== USERS PAGE =====
async function loadUsers(query = '') {
    try {
        const endpoint = query ? `/api/admin/users?q=${encodeURIComponent(query)}` : '/api/admin/users?limit=100';
        const users = await apiCall(endpoint);
        renderUsersTable(users);
    } catch (error) {
        console.error('Error loading users:', error);
    }
}

function renderUsersTable(users) {
    const tbody = document.getElementById('usersTableBody');
    
    if (!users || users.length === 0) {
        tbody.innerHTML = '<tr><td colspan="7" class="loading">No users found</td></tr>';
        return;
    }

    const admins = users.filter(u => u.role === 'admin');
    const normals = users.filter(u => u.role !== 'admin');

    const renderRow = (user) => {
        const intelKey = user.user_code || user.email || user.user_id; // prefer code, then email, then internal id

        return `
            <tr>
                <td>${user.user_code || '—'}</td>
                <td>${user.name || '—'}</td>
                <td>${user.email}</td>
                <td><span class="badge-status ${user.role === 'admin' ? 'badge-high' : 'badge-low'}">${user.role}</span></td>
                <td><span class="badge-status badge-${user.status}">${user.status}</span></td>
                <td>${user.created_at ? new Date(user.created_at).toLocaleDateString() : '—'}</td>
                <td>
                    <button class="btn-action btn-view" onclick="viewUserIntel('${intelKey}')">
                        View Intel
                    </button>
                </td>
            </tr>
        `;
    }
    let html = '';

    if (admins.length) {
        html += `
            <tr class="users-section-row">
                <td colspan="7">Admins</td>
            </tr>
            ${admins.map(renderRow).join('')}
        `;
    }

    if (normals.length) {
        html += `
            <tr class="users-section-row">
                <td colspan="7">Users</td>
            </tr>
            ${normals.map(renderRow).join('')}
        `;
    }

    tbody.innerHTML = html || '<tr><td colspan="7" class="loading">No users found</td></tr>';
}

function searchUsers(e) {
    const query = e.target.value;
    loadUsers(query);
}

window.viewUserIntel = (identifier) => {
    document.getElementById('intelUserId').value = identifier;
    navigateToPage('intelligence');
    setTimeout(() => searchIntelligence(), 300);
};

async function handleCreateUser(e) {
    e.preventDefault();

    const nameInput = document.getElementById('newUserName');
    const emailInput = document.getElementById('newUserEmail');
    const passwordInput = document.getElementById('newUserPassword');
    const roleSelect = document.getElementById('newUserRole');

    const name = nameInput.value.trim();
    const email = emailInput.value.trim();
    const password = passwordInput.value;
    const role = roleSelect.value || 'user';

    if (!name || !email || !password) {
        if (typeof showNotification === 'function') {
            showNotification('Name, email and password are required', 'warning');
        } else {
            alert('Name, email and password are required');
        }
        return;
    }

    try {
        const result = await apiCall('/auth/register', {
            method: 'POST',
            body: JSON.stringify({ name, email, password, role })
        });

        if (result && result.detail) {
            if (typeof showNotification === 'function') {
                showNotification(result.detail, 'error');
            } else {
                alert(result.detail);
            }
            return;
        }

        if (typeof showNotification === 'function') {
            const code = result.user_code || 'user';
            showNotification(`User ${result.name || result.email} (${code}) created successfully`, 'success');
        } else {
            alert(`User ${result.name || result.email} created successfully`);
        }

        document.getElementById('createUserForm').reset();

        const currentQuery = document.getElementById('userSearch')?.value || '';
        loadUsers(currentQuery);
    } catch (error) {
        console.error('Error creating user:', error);
        const msg = error?.message || 'Failed to create user';
        if (typeof showNotification === 'function') {
            showNotification(msg, 'error');
        } else {
            alert(msg);
        }
    }
}

// ===== ANALYTICS PAGE =====
async function loadAnalytics() {
    try {
        await loadGeoHotspots();
        await loadGlobalRiskTrend();
    } catch (error) {
        console.error('Error loading analytics:', error);
    }
}

async function loadGeoHotspots() {
    try {
        const days = document.getElementById('geoTimeRange')?.value || 30;
        const data = await apiCall(`/api/admin/geo-hotspots?days=${days}`);
        
        if (data.success && data.points.length > 0) {
            renderGeoMap(data.points);
        } else {
            console.log('No geo data available');
        }
    } catch (error) {
        console.error('Error loading geo hotspots:', error);
    }
}

function renderGeoMap(points) {
    const mapDiv = document.getElementById('geoMap');
    
    if (!geoMap) {
        geoMap = L.map('geoMap').setView([20, 0], 2);
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '© OpenStreetMap contributors'
        }).addTo(geoMap);
    } else {
        geoMap.eachLayer(layer => {
            if (layer instanceof L.Marker || layer instanceof L.Circle) {
                geoMap.removeLayer(layer);
            }
        });
    }

    points.forEach(point => {
        const riskColor = point.avg_risk >= 70 ? '#ef4444' :
                         point.avg_risk >= 50 ? '#f59e0b' :
                         point.avg_risk >= 30 ? '#3b82f6' : '#10b981';
        
        const radius = Math.max(point.txn_count * 1000, 50000);

        L.circle([point.lat, point.lon], {
            color: riskColor,
            fillColor: riskColor,
            fillOpacity: 0.4,
            radius: radius
        }).addTo(geoMap).bindPopup(`
            <strong>${point.city || point.country}</strong><br>
            Transactions: ${point.txn_count}<br>
            Avg Risk: ${point.avg_risk}<br>
            High Risk: ${point.high_risk_count}
        `);
    });
}

async function loadGlobalRiskTrend() {
    try {
        const data = await apiCall('/api/admin/risk-trend-global?days=30');
        
        if (data.success && data.days.length > 0) {
            renderVolumeChart(data.days);
            renderFraudTrendChart(data.days);
        }
    } catch (error) {
        console.error('Error loading global risk trend:', error);
    }
}

function renderVolumeChart(days) {
    const ctx = document.getElementById('volumeChart');
    
    if (charts.volume) {
        charts.volume.destroy();
    }

    charts.volume = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: days.map(d => d.date),
            datasets: [{
                label: 'Transaction Volume',
                data: days.map(d => d.total_txns),
                backgroundColor: 'rgba(99, 102, 241, 0.5)',
                borderColor: 'rgb(99, 102, 241)',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true
                }
            }
        }
    });
}

function renderFraudTrendChart(days) {
    const ctx = document.getElementById('fraudTrendChart');
    
    if (charts.fraudTrend) {
        charts.fraudTrend.destroy();
    }

    charts.fraudTrend = new Chart(ctx, {
        type: 'line',
        data: {
            labels: days.map(d => d.date),
            datasets: [{
                label: 'Avg Fraud Probability',
                data: days.map(d => d.avg_fraud_probability),
                borderColor: 'rgb(239, 68, 68)',
                backgroundColor: 'rgba(239, 68, 68, 0.1)',
                tension: 0.4,
                fill: true
            }, {
                label: 'High Risk Events',
                data: days.map(d => d.high_risk_events),
                borderColor: 'rgb(245, 158, 11)',
                backgroundColor: 'rgba(245, 158, 11, 0.1)',
                tension: 0.4,
                fill: true,
                yAxisID: 'y1'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true,
                    position: 'left'
                },
                y1: {
                    beginAtZero: true,
                    position: 'right',
                    grid: {
                        drawOnChartArea: false
                    }
                }
            }
        }
    });
}