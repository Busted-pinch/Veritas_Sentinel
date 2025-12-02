// ===== ALERTS PAGE ===== (Continuation of admin_dashboard.js)

async function loadAlerts() {
    try {
        const alerts = await apiCall('/api/admin/alerts');
        const filter = document.getElementById('alertFilter')?.value || 'all';
        
        const filtered = filter === 'all' 
            ? alerts 
            : alerts.filter(a => a.status === filter);
        
        renderAlertsTable(filtered);
    } catch (error) {
        console.error('Error loading alerts:', error);
    }
}

function renderAlertsTable(alerts) {
    const tbody = document.getElementById('alertsTableBody');
    
    if (alerts.length === 0) {
        tbody.innerHTML = '<tr><td colspan="7" class="loading">No alerts found</td></tr>';
        return;
    }

    tbody.innerHTML = alerts.map(alert => `
        <tr>
            <td>${alert.alert_id}</td>
            <td>${alert.user_id}</td>
            <td><span class="badge-status badge-${alert.risk_level}">${alert.risk_level}</span></td>
            <td>${alert.final_risk_score}</td>
            <td><span class="badge-status badge-${alert.status}">${alert.status}</span></td>
            <td>${new Date(alert.created_at).toLocaleString()}</td>
            <td>
                ${alert.status === 'open' ? 
                    `<button class="btn-action btn-resolve" onclick="openResolveModal('${alert.alert_id}')">Resolve</button>` :
                    `<span style="color: var(--gray); font-size: 13px;">Resolved</span>`
                }
            </td>
        </tr>
    `).join('');
}

window.openResolveModal = (alertId) => {
    currentAlertId = alertId;
    document.getElementById('alertModal').classList.add('show');
};

function closeModal() {
    document.getElementById('alertModal').classList.remove('show');
    currentAlertId = null;
}

async function confirmResolveAlert() {
    if (!currentAlertId) return;

    const status = document.getElementById('alertStatus').value;
    const note = document.getElementById('alertNote').value;

    try {
        await apiCall(`/api/admin/alerts/${currentAlertId}`, {
            method: 'PATCH',
            body: JSON.stringify({ status, note })
        });

        closeModal();
        loadAlerts();
        
        // Show success message
        showNotification('Alert resolved successfully', 'success');
    } catch (error) {
        console.error('Error resolving alert:', error);
        showNotification('Failed to resolve alert', 'error');
    }
}

// ===== INTELLIGENCE PAGE =====
async function searchIntelligence() {
    const userId = document.getElementById('intelUserId').value.trim();
    
    if (!userId) {
        showNotification('Please enter a User ID', 'warning');
        return;
    }

    try {
        const data = await apiCall('/api/agent/intel', {
            method: 'POST',
            body: JSON.stringify({ user_id: userId })
        });

        if (data.success) {
            renderIntelligenceResults(data);
        } else {
            showNotification(data.message || 'Failed to fetch intelligence', 'error');
        }
    } catch (error) {
        console.error('Error fetching intelligence:', error);
        showNotification('Error fetching intelligence data', 'error');
    }
}

function renderIntelligenceResults(data) {
    document.getElementById('intelResults').style.display = 'block';

    // Profile
    renderIntelProfile(data.profile, data.metrics);

    // Risk Trend
    if (data.trend_30d && data.trend_30d.length > 0) {
        renderIntelRiskChart(data.trend_30d);
    }

    // AI Analysis
    renderAiAnalysis(data.summary);

    // Transactions
    renderIntelTransactions(data.recent_transactions);

    // Alerts
    renderIntelAlerts(data.alerts);
}

function renderIntelProfile(profile, metrics) {
    const div = document.getElementById('intelProfile');
    
    if (!profile) {
        div.innerHTML = '<p style="color: var(--gray);">No profile data available</p>';
        return;
    }

    div.innerHTML = `
        <div style="display: grid; gap: 12px;">
            <div class="profile-stat">
                <span style="color: var(--gray); font-size: 13px;">Trust Score</span>
                <span style="font-size: 24px; font-weight: 700; color: ${getTrustColor(profile.trust_score)}">${profile.trust_score?.toFixed(1) || 'N/A'}</span>
            </div>
            <div class="profile-stat">
                <span style="color: var(--gray); font-size: 13px;">Avg Amount</span>
                <span style="font-size: 18px; font-weight: 600;">₹${profile.amount_stats?.avg?.toFixed(2) || 0}</span>
            </div>
            <div class="profile-stat">
                <span style="color: var(--gray); font-size: 13px;">Avg Risk</span>
                <span style="font-size: 18px; font-weight: 600;">${profile.risk_stats?.avg_risk_score?.toFixed(2) || 0}</span>
            </div>
            <div class="profile-stat">
                <span style="color: var(--gray); font-size: 13px;">High Risk Txns</span>
                <span style="font-size: 18px; font-weight: 600;">${profile.risk_stats?.high_risk_txn_count || 0}</span>
            </div>
            <div class="profile-stat">
                <span style="color: var(--gray); font-size: 13px;">Total Transactions</span>
                <span style="font-size: 18px; font-weight: 600;">${profile.risk_stats?.total_txn_count || 0}</span>
            </div>
        </div>
    `;
}

function getTrustColor(score) {
    if (score >= 80) return 'var(--success)';
    if (score >= 60) return 'var(--primary)';
    if (score >= 40) return 'var(--warning)';
    return 'var(--danger)';
}

function renderIntelRiskChart(trend) {
    const ctx = document.getElementById('intelRiskChart');
    
    if (charts.intelRisk) {
        charts.intelRisk.destroy();
    }

    charts.intelRisk = new Chart(ctx, {
        type: 'line',
        data: {
            labels: trend.map(d => d.date),
            datasets: [{
                label: 'Avg Risk',
                data: trend.map(d => d.avg_risk),
                borderColor: 'rgb(239, 68, 68)',
                backgroundColor: 'rgba(239, 68, 68, 0.1)',
                tension: 0.4,
                fill: true
            }, {
                label: 'Trust Score',
                data: trend.map(d => d.trust_score),
                borderColor: 'rgb(16, 185, 129)',
                backgroundColor: 'rgba(16, 185, 129, 0.1)',
                tension: 0.4,
                fill: true
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true,
                    max: 100
                }
            }
        }
    });
}

function renderAiAnalysis(summary) {
    const div = document.getElementById('intelAiAnalysis');
    
    if (!summary) {
        div.innerHTML = '<p style="color: var(--gray);">No AI analysis available</p>';
        return;
    }

    let html = '<div style="display: grid; gap: 20px;">';

    // Behavior Summary
    if (summary.behaviour) {
        const behaviour = typeof summary.behaviour === 'string' 
            ? JSON.parse(summary.behaviour) 
            : summary.behaviour;
        
        html += `
            <div class="ai-section">
                <h5 style="color: var(--primary); margin-bottom: 8px;">Behavior Analysis</h5>
                <p style="color: var(--dark); margin-bottom: 8px;"><strong>Verdict:</strong> ${behaviour.verdict || 'N/A'}</p>
                <p style="color: var(--gray); font-size: 14px; line-height: 1.6;">${behaviour.summary || 'No summary available'}</p>
                ${behaviour.key_patterns && behaviour.key_patterns.length > 0 ? `
                    <ul style="margin-top: 8px; padding-left: 20px;">
                        ${behaviour.key_patterns.map(p => `<li style="color: var(--gray); font-size: 13px;">${p}</li>`).join('')}
                    </ul>
                ` : ''}
            </div>
        `;
    }

    // Speculation
    if (summary.speculation) {
        const speculation = typeof summary.speculation === 'string' 
            ? JSON.parse(summary.speculation) 
            : summary.speculation;
        
        html += `
            <div class="ai-section">
                <h5 style="color: var(--warning); margin-bottom: 8px;">Speculation Score</h5>
                <p style="font-size: 24px; font-weight: 700; margin-bottom: 8px;">${speculation.speculation_score || 'N/A'}/100</p>
                <p style="color: var(--gray); font-size: 14px; line-height: 1.6;">${speculation.explanation || 'No explanation available'}</p>
                ${speculation.indicators && speculation.indicators.length > 0 ? `
                    <ul style="margin-top: 8px; padding-left: 20px;">
                        ${speculation.indicators.map(i => `<li style="color: var(--gray); font-size: 13px;">${i}</li>`).join('')}
                    </ul>
                ` : ''}
            </div>
        `;
    }

    // Investigation
    if (summary.investigation) {
        const investigation = typeof summary.investigation === 'string' 
            ? JSON.parse(summary.investigation) 
            : summary.investigation;
        
        html += `
            <div class="ai-section">
                <h5 style="color: var(--danger); margin-bottom: 8px;">Investigation Case File</h5>
                <p style="color: var(--gray); font-size: 14px; line-height: 1.6; margin-bottom: 8px;">${investigation.executive_summary || 'No summary available'}</p>
                <p><strong>Risk Rating:</strong> <span class="badge-status badge-${investigation.risk_rating}">${investigation.risk_rating || 'N/A'}</span></p>
                <p style="margin-top: 8px;"><strong>Recommended Action:</strong> ${investigation.recommended_action || 'N/A'}</p>
            </div>
        `;
    }

    html += '</div>';
    div.innerHTML = html;
}

function renderIntelTransactions(transactions) {
    const div = document.getElementById('intelTransactions');
    
    if (!transactions || transactions.length === 0) {
        div.innerHTML = '<p style="color: var(--gray); font-size: 14px;">No recent transactions</p>';
        return;
    }

    div.innerHTML = `
        <div style="display: grid; gap: 12px; max-height: 400px; overflow-y: auto;">
            ${transactions.slice(0, 10).map(txn => `
                <div style="padding: 12px; background: var(--bg); border-radius: 8px; border-left: 3px solid ${getRiskLevelColor(txn.risk_level)};">
                    <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">
                        <span style="font-weight: 600; font-size: 13px;">${txn.txn_id}</span>
                        <span class="badge-status badge-${txn.risk_level}">${txn.risk_level}</span>
                    </div>
                    <div style="font-size: 12px; color: var(--gray);">
                        <p>Amount: ₹${txn.amount} ${txn.currency || ''}</p>
                        <p>Risk: ${txn.final_risk_score} | Fraud Prob: ${txn.fraud_probability}</p>
                        <p>${new Date(txn.timestamp).toLocaleString()}</p>
                    </div>
                </div>
            `).join('')}
        </div>
    `;
}

function renderIntelAlerts(alerts) {
    const div = document.getElementById('intelAlerts');
    
    if (!alerts || alerts.length === 0) {
        div.innerHTML = '<p style="color: var(--gray); font-size: 14px;">No recent alerts</p>';
        return;
    }

    div.innerHTML = `
        <div style="display: grid; gap: 12px; max-height: 400px; overflow-y: auto;">
            ${alerts.slice(0, 10).map(alert => `
                <div style="padding: 12px; background: var(--bg); border-radius: 8px; border-left: 3px solid ${getRiskLevelColor(alert.risk_level)};">
                    <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">
                        <span style="font-weight: 600; font-size: 13px;">${alert.alert_id}</span>
                        <span class="badge-status badge-${alert.status}">${alert.status}</span>
                    </div>
                    <div style="font-size: 12px; color: var(--gray);">
                        <p>Risk Level: <span class="badge-status badge-${alert.risk_level}">${alert.risk_level}</span></p>
                        <p>Score: ${alert.final_risk_score}</p>
                        <p>${new Date(alert.created_at).toLocaleString()}</p>
                    </div>
                </div>
            `).join('')}
        </div>
    `;
}

function getRiskLevelColor(level) {
    const colors = {
        low: 'var(--primary)',
        medium: 'var(--warning)',
        high: 'rgb(249, 115, 22)',
        critical: 'var(--danger)'
    };
    return colors[level] || 'var(--gray)';
}

// ===== UTILITIES =====
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

function showNotification(message, type = 'info') {
    // Simple notification - you can enhance this with a toast library
    const colors = {
        success: 'var(--success)',
        error: 'var(--danger)',
        warning: 'var(--warning)',
        info: 'var(--primary)'
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