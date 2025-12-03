const API_BASE = 'http://localhost:8000';

// Auth check
const token = localStorage.getItem('token');
const user = JSON.parse(localStorage.getItem('user') || '{}');

if (!token || !user.user_id) {
    window.location.href = 'login.html';
}

// Global state
let riskChart = null;
let currentPage = 'dashboard';

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    initializePage();
    setupEventListeners();
    loadDashboardData();
});

// ===== UPDATED initializePage (capitalized username) =====
function initializePage() {
    // Extract and capitalize username
    const userEmail = user.email || '';
    const userName = userEmail.split('@')[0] || 'User';
    const capitalizedName = userName.charAt(0).toUpperCase() + userName.slice(1);
    
    // Set in sidebar
    document.getElementById('userName').textContent = capitalizedName;
    document.getElementById('userInitials').textContent = userName.charAt(0).toUpperCase();
    
    // Set in welcome banner
    document.getElementById('welcomeName').textContent = capitalizedName;
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

    // Logout
    document.getElementById('logoutBtn').addEventListener('click', () => {
        localStorage.clear();
        window.location.href = 'login.html';
    });

    // Refresh
    document.getElementById('refreshBtn').addEventListener('click', () => {
        if (currentPage === 'dashboard') {
            loadDashboardData();
        }
    });

    // Transaction form
    document.getElementById('transactionForm').addEventListener('submit', handleTransactionSubmit);
    document.getElementById('resetForm').addEventListener('click', resetTransactionForm);
    document.getElementById('closeResult')?.addEventListener('click', () => {
        document.getElementById('resultCard').style.display = 'none';
    });
}

function navigateToPage(page) {
    currentPage = page;

    document.querySelectorAll('.nav-item').forEach(item => {
        item.classList.toggle('active', item.dataset.page === page);
    });

    document.querySelectorAll('.page-content').forEach(content => {
        content.classList.toggle('active', content.id === `${page}Page`);
    });

    const titles = {
        dashboard: 'Dashboard',
        'new-transaction': 'New Transaction',
    };
    document.getElementById('pageTitle').textContent = titles[page] || page;
}

// ===== API HELPER =====
async function apiCall(endpoint, options = {}) {
    const response = await fetch(`${API_BASE}${endpoint}`, {
        ...options,
        headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
            ...options.headers,
        },
    });

    if (response.status === 401) {
        localStorage.clear();
        window.location.href = 'login.html';
        throw new Error('Unauthorized');
    }

    return response.json();
}

// ===== DASHBOARD DATA =====
async function loadDashboardData() {
    console.log('Loading dashboard data...');

    // helper to safely call an endpoint without killing everything
    const safeCall = async (label, endpoint) => {
        try {
            const data = await apiCall(endpoint);
            console.log(`${label} OK:`, data);
            return data;
        } catch (err) {
            console.error(`${label} FAILED for ${endpoint}`, err);
            return null; // let UI handle missing piece
        }
    };

    const [
        summary,
        trend,
        history,
        alerts
    ] = await Promise.all([
        safeCall('summary', '/api/transactions/me/summary'),
        safeCall('trend', '/api/transactions/me/risk-trend'),
        safeCall('history', '/api/transactions/me/history?limit=10'),
        safeCall('alerts', '/api/transactions/me/alerts?limit=10'),
    ]);

    if (!summary) {
        // only shout at user if the *core* summary failed
        showNotification('Failed to load dashboard summary', 'error');
    }

    updateDashboardUI(summary, trend, history, alerts);
}


function updateDashboardUI(summaryData, trendData, historyData, alertsData) {
    if (!summaryData || !summaryData.success) return;

    const profile = summaryData.profile;

            // ---- Trust score ring ----
            console.log('Summary data in updateDashboardUI:', summaryData);

            if (profile && profile.trust_score !== undefined) {
                let trustScore = profile.trust_score;
                trustScore = Math.max(0, Math.min(100, trustScore));

                const trustScoreEl = document.getElementById('trustScoreValue');
                const circle = document.getElementById('trustProgressCircle');

                console.log('Trust score:', trustScore, 'circle element:', circle);

                if (trustScoreEl) {
                    trustScoreEl.textContent = trustScore.toFixed(0);
                }

                if (circle) {
                    const radius = circle.r.baseVal.value;        // should be 42
                    const circumference = 2 * Math.PI * radius;

                    circle.style.strokeDasharray = `${circumference} ${circumference}`;
                    const offset = circumference * (1 - trustScore / 100);
                    circle.style.strokeDashoffset = offset;

                    if (trustScore >= 80) circle.style.stroke = '#10b981';
                    else if (trustScore >= 60) circle.style.stroke = '#3b82f6';
                    else if (trustScore >= 40) circle.style.stroke = '#f59e0b';
                    else circle.style.stroke = '#ef4444';
                }
            }



    // ---- Stats cards ----
    if (profile) {
        const riskStats = profile.risk_stats || {};
        const amountStats = profile.amount_stats || {};

        document.getElementById('totalTxns').textContent =
            riskStats.total_txn_count || 0;
        document.getElementById('avgRisk').textContent =
            (riskStats.avg_risk_score || 0).toFixed(1);
        document.getElementById('avgAmount').textContent =
            '₹' + (amountStats.avg || 0).toFixed(2);
        document.getElementById('highRiskCount').textContent =
            riskStats.high_risk_txn_count || 0;
    }

    // ---- Balance ----
    if (typeof summaryData.balance === 'number') {
        document.getElementById('balanceValue').textContent =
            '₹' + summaryData.balance.toFixed(2);
    }

    // ---- Risk trend chart ----
    if (trendData && trendData.success && Array.isArray(trendData.days) && trendData.days.length > 0) {
        renderRiskTrendChart(trendData.days);
    } else {
        const chartContainer = document.querySelector('#riskTrendChart').parentElement;
        chartContainer.innerHTML =
            '<p style="text-align: center; color: var(--gray); padding: 40px;">No transaction history available yet. Start by creating your first transaction!</p>';
    }

    // ---- Recent transactions ----
    if (historyData && historyData.success) {
        renderRecentTransactions(historyData.transactions || []);
    }

    // ---- Recent alerts ----
    if (alertsData && alertsData.success) {
        renderRecentAlerts(alertsData.alerts || []);
    }
}

function renderRiskTrendChart(days) {
    const canvas = document.getElementById('riskTrendChart');

    // clamp height so it doesn’t stretch the whole page
    canvas.style.height = '260px';
    canvas.height = 260;

    if (riskChart) {
        riskChart.destroy();
    }

    riskChart = new Chart(canvas, {
        type: 'line',
        data: {
            labels: days.map(d => d.date),
            datasets: [
                {
                    label: 'Average Risk Score',
                    data: days.map(d => d.avg_risk),
                    borderColor: 'rgb(239, 68, 68)',
                    backgroundColor: 'rgba(239, 68, 68, 0.1)',
                    tension: 0.4,
                    fill: true,
                },
                {
                    label: 'Trust Score',
                    data: days.map(d => d.trust_score),
                    borderColor: 'rgb(16, 185, 129)',
                    backgroundColor: 'rgba(16, 185, 129, 0.1)',
                    tension: 0.4,
                    fill: true,
                },
            ],
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: true,
                    position: 'top',
                },
            },
            scales: {
                y: {
                    beginAtZero: true,
                    max: 100,
                },
            },
        },
    });
}

// ===== UPDATED renderRecentTransactions (capitalized type) =====
function renderRecentTransactions(transactions) {
    const tbody = document.getElementById('recentTxBody');

    if (!transactions || transactions.length === 0) {
        tbody.innerHTML =
            '<tr><td colspan="6" class="loading">No transactions yet</td></tr>';
        return;
    }

    tbody.innerHTML = transactions
        .map(txn => {
            const riskLevel = txn.risk_level || 'low';
            const riskClass = `badge-status badge-${riskLevel}`;
            const when = txn.timestamp
                ? new Date(txn.timestamp).toLocaleString()
                : '—';
            const amount = typeof txn.amount === 'number'
                ? `₹${txn.amount.toFixed(2)}`
                : '—';
            
            // Capitalize transaction type
            const txnType = (txn.txn_type || 'withdraw').toLowerCase();
            const capitalizedType = txnType.charAt(0).toUpperCase() + txnType.slice(1);

            return `
            <tr>
                <td>${txn.txn_id || '—'}</td>
                <td><span style="font-weight: 600;">${capitalizedType}</span></td>
                <td>${amount}</td>
                <td>${txn.channel || '—'}</td>
                <td>
                    <span class="${riskClass}">
                        ${riskLevel}
                    </span>
                </td>
                <td>${when}</td>
            </tr>
        `;
        })
        .join('');
}

function renderRecentAlerts(alerts) {
    const tbody = document.getElementById('recentAlertBody');

    if (!alerts || alerts.length === 0) {
        tbody.innerHTML =
            '<tr><td colspan="5" class="loading">No alerts yet</td></tr>';
        return;
    }

    tbody.innerHTML = alerts
        .map(alert => {
            const riskLevel = alert.risk_level || 'low';
            const riskClass = `badge-status badge-${riskLevel}`;
            const status = alert.status || 'open';
            const statusClass = `badge-status badge-${status}`;
            const when = alert.created_at
                ? new Date(alert.created_at).toLocaleString()
                : '—';

            return `
            <tr>
                <td>${alert.alert_id || '—'}</td>
                <td><span class="${riskClass}">${riskLevel}</span></td>
                <td>${alert.final_risk_score?.toFixed?.(1) ?? '—'}</td>
                <td><span class="${statusClass}">${status}</span></td>
                <td>${when}</td>
            </tr>
        `;
        })
        .join('');
}

// ===== TRANSACTION FORM =====
async function handleTransactionSubmit(e) {
    e.preventDefault();

    const form = e.target;
    const formData = new FormData(form);

    const txnType = (formData.get('txnType') || 'WITHDRAW').toString().toUpperCase();

    const transaction = {
        user_id: user.user_id, // backend ignores this & uses token, but fine
        amount: parseFloat(formData.get('amount')),
        channel: formData.get('channel'),
        currency: formData.get('currency') || 'INR',
        merchant_type: formData.get('merchantType') || null,
        timestamp: new Date().toISOString(),
        txn_type: txnType,
    };

    const city = formData.get('city');
    const country = formData.get('country');
    const lat = formData.get('latitude');
    const lon = formData.get('longitude');

    if (city || country || lat || lon) {
        transaction.location = {
            city: city || null,
            country: country || 'India',
            lat: lat ? parseFloat(lat) : null,
            lon: lon ? parseFloat(lon) : null,
        };
    }

    const deviceType = formData.get('deviceType');
    const deviceOS = formData.get('deviceOS');

    if (deviceType || deviceOS) {
        transaction.device = {
            device_type: deviceType || null,
            os: deviceOS || null,
        };
    }

    document.getElementById('loaderOverlay').classList.add('show');

    try {
        const result = await apiCall('/api/transaction/new', {
            method: 'POST',
            body: JSON.stringify(transaction),
        });

        if (result.success) {
            displayTransactionResult(result);
            form.reset();
            showNotification('Transaction processed successfully!', 'success');

            // Refresh dashboard stats (balance, history, trend)
            loadDashboardData();
        } else {
            showNotification(
                'Transaction failed: ' + (result.message || 'Unknown error'),
                'error'
            );
        }
    } catch (error) {
        console.error('Transaction error:', error);
        showNotification(
            'Failed to process transaction. Please try again.',
            'error'
        );
    } finally {
        document.getElementById('loaderOverlay').classList.remove('show');
    }
}

function resetTransactionForm() {
    document.getElementById('transactionForm').reset();
}

function displayTransactionResult(result) {
    const resultCard = document.getElementById('resultCard');
    const resultContent = document.getElementById('resultContent');

    const scores = result.ml_scores || {};
    const riskLevel = scores.risk_level || 'low';
    const riskScore = scores.final_risk_score || 0;
    const fraudProb = scores.fraud_probability || 0;
    const anomalyScore = scores.anomaly_score || 0;

    console.log('Result scores:', { riskLevel, riskScore, fraudProb, anomalyScore });

    const riskColor = getRiskLevelColor(riskLevel);

    resultContent.innerHTML = `
        <div style="display: grid; gap: 24px;">
            <div style="text-align: center; padding: 24px; background: ${riskColor}15; border-radius: 12px; border: 2px solid ${riskColor};">
                <h3 style="color: ${riskColor}; font-size: 48px; font-weight: 700; margin-bottom: 8px;">${riskScore.toFixed(1)}</h3>
                <p style="color: var(--gray); text-transform: uppercase; font-size: 14px; font-weight: 600; letter-spacing: 1px;">Risk Score</p>
                <p style="margin-top: 12px;">
                    <span style="display: inline-block; padding: 6px 16px; background: ${riskColor}; color: white; border-radius: 20px; font-weight: 600; text-transform: uppercase;">
                        ${riskLevel}
                    </span>
                </p>
            </div>

            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 16px;">
                <div style="padding: 20px; background: var(--dark-card); border-radius: 12px;">
                    <p style="color: var(--gray); font-size: 13px; margin-bottom: 4px;">Fraud Probability</p>
                    <p style="font-size: 24px; font-weight: 700; color: var(--white);">
                        ${fraudProb.toFixed(1)}%
                    </p>
                </div>

                <div style="padding: 20px; background: var(--dark-card); border-radius: 12px;">
                    <p style="color: var(--gray); font-size: 13px; margin-bottom: 4px;">Anomaly Score</p>
                    <p style="font-size: 24px; font-weight: 700; color: var(--white);">
                        ${anomalyScore.toFixed(1)}
                    </p>
                </div>

                <div style="padding: 20px; background: var(--dark-card); border-radius: 12px;">
                    <p style="color: var(--gray); font-size: 13px; margin-bottom: 4px;">Trust Score</p>
                    <p style="font-size: 24px; font-weight: 700; color: var(--white);">
                        ${(scores.trust_score || 0).toFixed(1)}
                    </p>
                </div>
            </div>
        </div>
    `;

    resultCard.style.display = 'block';
}

function getRiskLevelColor(level) {
    switch (level) {
        case 'critical':
            return '#ef4444';
        case 'high':
            return '#f97316';
        case 'medium':
            return '#f59e0b';
        case 'low':
        default:
            return '#3b82f6';
    }
}

// ===== NOTIFICATIONS =====
function showNotification(message, type = 'info') {
    const colors = {
        success: 'var(--success)',
        error: 'var(--danger)',
        warning: 'var(--warning)',
        info: 'var(--primary)',
    };

    const notification = document.createElement('div');
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 16px 24px;
        background: ${colors[type]};
        color: white;
        border-radius: 12px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        z-index: 10000;
        animation: slideIn 0.3s ease;
    `;
    notification.textContent = message;

    document.body.appendChild(notification);

    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}
