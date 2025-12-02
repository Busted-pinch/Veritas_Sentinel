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

function initializePage() {
    // Set user info
    const userName = user.email?.split('@')[0] || 'User';
    document.getElementById('userName').textContent = userName;
    document.getElementById('userInitials').textContent = (user.email?.[0] || 'U').toUpperCase();
    document.getElementById('welcomeName').textContent = userName;
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
        dashboard: 'Dashboard',
        'new-transaction': 'New Transaction'
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

// ===== DASHBOARD DATA =====
async function loadDashboardData() {
    try {
        // Get user profile and risk trend
        const [profile, riskTrend] = await Promise.all([
            getUserProfile(),
            getRiskTrend()
        ]);

        updateDashboardUI(profile, riskTrend);
    } catch (error) {
        console.error('Error loading dashboard data:', error);
        showNotification('Failed to load dashboard data', 'error');
    }
}

async function getUserProfile() {
    try {
        const data = await apiCall('/api/agent/intel', {
            method: 'POST',
            body: JSON.stringify({ user_id: user.user_id })
        });
        
        if (data.success) {
            return data;
        }
        return null;
    } catch (error) {
        console.error('Error fetching profile:', error);
        return null;
    }
}

async function getRiskTrend() {
    try {
        return await apiCall(`/api/agent/risk-trend/${user.user_id}`);
    } catch (error) {
        console.error('Error fetching risk trend:', error);
        return null;
    }
}

function updateDashboardUI(profileData, trendData) {
    if (!profileData) return;

    const profile = profileData.profile;
    
    // Update trust score with animation
    if (profile && profile.trust_score !== undefined) {
        const trustScore = profile.trust_score;
        document.getElementById('trustScoreValue').textContent = trustScore.toFixed(0);
        
        // Animate trust ring
        const circle = document.getElementById('trustProgressCircle');
        const circumference = 283;
        const offset = circumference - (trustScore / 100) * circumference;
        circle.style.strokeDashoffset = offset;
        
        // Color based on score
        if (trustScore >= 80) {
            circle.style.stroke = '#10b981';
        } else if (trustScore >= 60) {
            circle.style.stroke = '#3b82f6';
        } else if (trustScore >= 40) {
            circle.style.stroke = '#f59e0b';
        } else {
            circle.style.stroke = '#ef4444';
        }
    }

    // Update stats
    if (profile) {
        const riskStats = profile.risk_stats || {};
        const amountStats = profile.amount_stats || {};
        
        document.getElementById('totalTxns').textContent = riskStats.total_txn_count || 0;
        document.getElementById('avgRisk').textContent = (riskStats.avg_risk_score || 0).toFixed(1);
        document.getElementById('avgAmount').textContent = '₹' + (amountStats.avg || 0).toFixed(2);
        document.getElementById('highRiskCount').textContent = riskStats.high_risk_txn_count || 0;
    }

    // Render risk trend chart
    if (trendData && trendData.success && trendData.days && trendData.days.length > 0) {
        renderRiskTrendChart(trendData.days);
    } else {
        // Show message if no data
        const chartContainer = document.querySelector('#riskTrendChart').parentElement;
        chartContainer.innerHTML = '<p style="text-align: center; color: var(--gray); padding: 40px;">No transaction history available yet. Start by creating your first transaction!</p>';
    }
}

function renderRiskTrendChart(days) {
    const ctx = document.getElementById('riskTrendChart');
    
    if (riskChart) {
        riskChart.destroy();
    }

    riskChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: days.map(d => d.date),
            datasets: [{
                label: 'Average Risk Score',
                data: days.map(d => d.avg_risk),
                borderColor: 'rgb(239, 68, 68)',
                backgroundColor: 'rgba(239, 68, 68, 0.1)',
                tension: 0.4,
                fill: true
            }, {
                label: 'Trust Score',
                data: days.map(d => d.trust_score),
                borderColor: 'rgb(16, 185, 129)',
                backgroundColor: 'rgba(16, 185, 129, 0.1)',
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

// ===== TRANSACTION FORM =====
async function handleTransactionSubmit(e) {
    e.preventDefault();
    
    const form = e.target;
    const formData = new FormData(form);
    
    // Build transaction object
    const transaction = {
        user_id: user.user_id,
        amount: parseFloat(formData.get('amount')),
        channel: formData.get('channel'),
        currency: formData.get('currency') || 'INR',
        merchant_type: formData.get('merchantType') || null,
        timestamp: new Date().toISOString()
    };

    // Add location if provided
    const city = formData.get('city');
    const country = formData.get('country');
    const lat = formData.get('latitude');
    const lon = formData.get('longitude');
    
    if (city || country || lat || lon) {
        transaction.location = {
            city: city || null,
            country: country || 'India',
            lat: lat ? parseFloat(lat) : null,
            lon: lon ? parseFloat(lon) : null
        };
    }

    // Add device if provided
    const deviceType = formData.get('deviceType');
    const deviceOS = formData.get('deviceOS');
    
    if (deviceType || deviceOS) {
        transaction.device = {
            device_type: deviceType || null,
            os: deviceOS || null
        };
    }

    // Show loader
    document.getElementById('loaderOverlay').classList.add('show');

    try {
        const result = await apiCall('/api/transaction/new', {
            method: 'POST',
            body: JSON.stringify(transaction)
        });

        if (result.success) {
            displayTransactionResult(result);
            form.reset();
            
            // Show success notification
            showNotification('Transaction processed successfully!', 'success');
        } else {
            showNotification('Transaction failed: ' + (result.message || 'Unknown error'), 'error');
        }
    } catch (error) {
        console.error('Transaction error:', error);
        showNotification('Failed to process transaction. Please try again.', 'error');
    } finally {
        document.getElementById('loaderOverlay').classList.remove('show');
    }
}

function displayTransactionResult(result) {
    const resultCard = document.getElementById('resultCard');
    const resultContent = document.getElementById('resultContent');
    
    const scores = result.ml_scores || {};
    const riskLevel = scores.risk_level || 'unknown';
    const riskScore = scores.final_risk_score || 0;
    const fraudProb = scores.fraud_probability || 0;
    const anomalyScore = scores.anomaly_score || 0;
    
    // Get color based on risk level
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
                <div style="padding: 20px; background: var(--bg); border-radius: 12px;">
                    <p style="color: var(--gray); font-size: 13px; margin-bottom: 4px;">Fraud Probability</p>
                    <p style="font-size: 24px; font-weight: 700; color: var(--dark);">${fraudProb.toFixed(1)}%</p>
                </div>
                
                <div style="padding: 20px; background: var(--bg); border-radius: 12px;">
                    <p style="color: var(--gray); font-size: 13px; margin-bottom: 4px;">Anomaly Score</p>
                    <p style="font-size: 24px; font-weight: 700; color: var(--dark);">${anomalyScore.toFixed(1)}</p>
                </div>
                
                <div style="padding: 20px; background: var(--bg); border-radius: 12px;">
                    <p style="color: var(--gray); font-size: 13px; margin-bottom: 4px;">Trust Score</p>
                    <p style="font-size: 24px; font-weight: 700; color: var(--dark);">${(scores.trust_score || 0).toFixed(1)}</p>
                </div>
            </div>

            <div style="padding: 20px; background: #dbeafe; border-radius: 12px; border-left: 4px solid var(--primary);">
                <h4 style="margin-bottom: 8px; color: var(--dark);">Transaction Details</h4>
                <p style="font-size: 14px; color: var(--gray); margin-bottom: 4px;"><strong>Transaction ID:</strong> ${result.txn_id}</p>
                <p style="font-size: 14px; color: var(--gray); margin-bottom: 4px;"><strong>Updated Trust Score:</strong> ${(result.updated_profile?.trust_score || 0).toFixed(1)}</p>
                ${result.risk_alert_id ? 
                    `<p style="font-size: 14px; color: var(--danger); margin-top: 12px;">⚠️ This transaction triggered a risk alert (ID: ${result.risk_alert_id})</p>` 
                    : ''}
            </div>

            ${riskLevel === 'high' || riskLevel === 'critical' ? `
                <div style="padding: 20px; background: #fee; border-radius: 12px; border-left: 4px solid var(--danger);">
                    <h4 style="margin-bottom: 8px; color: var(--danger);">⚠️ High Risk Alert</h4>
                    <p style="font-size: 14px; color: var(--gray);">This transaction has been flagged for review due to elevated risk factors. Our security team has been notified.</p>
                </div>
            ` : ''}
        </div>
    `;
    
    resultCard.style.display = 'block';
    
    // Scroll to result
    resultCard.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

function getRiskLevelColor(level) {
    const colors = {
        low: '#3b82f6',
        medium: '#f59e0b',
        high: '#f97316',
        critical: '#ef4444'
    };
    return colors[level] || '#64748b';
}

function resetTransactionForm() {
    document.getElementById('transactionForm').reset();
    document.getElementById('resultCard').style.display = 'none';
}

// ===== UTILITIES =====
function showNotification(message, type = 'info') {
    const colors = {
        success: '#10b981',
        error: '#ef4444',
        warning: '#f59e0b',
        info: '#3b82f6'
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
        max-width: 400px;
    `;
    notification.textContent = message;

    const style = document.createElement('style');
    style.textContent = `
        @keyframes slideIn {
            from {
                opacity: 0;
                transform: translateX(100px);
            }
            to {
                opacity: 1;
                transform: translateX(0);
            }
        }
        @keyframes slideOut {
            from {
                opacity: 1;
                transform: translateX(0);
            }
            to {
                opacity: 0;
                transform: translateX(100px);
            }
        }
    `;
    document.head.appendChild(style);

    document.body.appendChild(notification);

    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => {
            notification.remove();
            style.remove();
        }, 300);
    }, 3000);
}