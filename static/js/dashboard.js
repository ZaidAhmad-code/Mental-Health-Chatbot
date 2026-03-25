/**
 * Serene AI - Analytics Dashboard
 * Visualizes user mental health trends using Chart.js
 * Adaptive to Light and Dark modes
 */

let charts = {};

document.addEventListener('DOMContentLoaded', function () {
    initDashboard();

    // Listen for theme changes
    window.addEventListener('themeChanged', () => {
        updateChartColors();
    });
});

function initDashboard() {
    // Initial data load
    updateStats();
    renderAllCharts();
}

function getThemeColors() {
    const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
    return {
        text: isDark ? '#E8E4DF' : '#1A2820',
        grid: isDark ? 'rgba(107, 155, 122, 0.15)' : 'rgba(45, 90, 61, 0.1)',
        muted: isDark ? '#7A7873' : '#5A6E62',
        accent: isDark ? '#6B9B7A' : '#2D5A3D',
        secondary: isDark ? '#8FB996' : '#3E7A52',
        accentBg: isDark ? 'rgba(107, 155, 122, 0.2)' : 'rgba(45, 90, 61, 0.15)'
    };
}

function getChartOptions() {
    const colors = getThemeColors();
    const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
    return {
        responsive: true,
        maintainAspectRatio: false,
        animation: {
            duration: 1000,
            easing: 'easeInOutQuart'
        },
        plugins: {
            legend: {
                display: true,
                position: 'top',
                align: 'end',
                labels: {
                    color: colors.text,
                    usePointStyle: true,
                    pointStyle: 'circle',
                    padding: 20,
                    font: { family: "'Inter', sans-serif", size: 12, weight: '500' }
                }
            },
            tooltip: {
                backgroundColor: isDark ? '#242B27' : '#FFFFFF',
                titleColor: colors.text,
                bodyColor: colors.text,
                borderColor: colors.accent,
                borderWidth: 2,
                padding: 12,
                cornerRadius: 12,
                displayColors: true,
                usePointStyle: true
            }
        },
        scales: {
            y: {
                grid: { color: colors.grid, drawBorder: false },
                ticks: { color: colors.muted, font: { size: 11 } },
                beginAtZero: true
            },
            x: {
                grid: { display: false },
                ticks: { color: colors.muted, font: { size: 11 } }
            }
        }
    };
}

function updateChartColors() {
    const options = getChartOptions();
    const colors = getThemeColors();

    Object.values(charts).forEach(chart => {
        // Update scales
        if (chart.options.scales) {
            if (chart.options.scales.x) {
                chart.options.scales.x.ticks.color = colors.muted;
            }
            if (chart.options.scales.y) {
                chart.options.scales.y.ticks.color = colors.muted;
                chart.options.scales.y.grid.color = colors.grid;
            }
        }

        // Update legend
        if (chart.options.plugins && chart.options.plugins.legend) {
            chart.options.plugins.legend.labels.color = colors.text;
        }

        // Update tooltips
        if (chart.options.plugins && chart.options.plugins.tooltip) {
            chart.options.plugins.tooltip.backgroundColor = document.documentElement.getAttribute('data-theme') === 'dark' ? '#242B27' : '#FFFFFF';
            chart.options.plugins.tooltip.titleColor = colors.text;
            chart.options.plugins.tooltip.bodyColor = colors.text;
        }

        chart.update();
    });
}

async function renderAllCharts() {
    const moodCtx = document.getElementById('moodChart').getContext('2d');
    const assessmentCtx = document.getElementById('assessmentChart').getContext('2d');
    const crisisCtx = document.getElementById('crisisChart').getContext('2d');
    const activityCtx = document.getElementById('activityChart').getContext('2d');

    loadMoodTrends(moodCtx);
    loadAssessmentTrends(assessmentCtx);
    loadCrisisPatterns(crisisCtx);
    loadEngagementMetrics(activityCtx);
}

async function updateStats() {
    try {
        const response = await fetch('/api/analytics/user-stats');
        const data = await response.json();

        document.getElementById('stat-total-messages').innerText = data.total_conversations || 0;
        document.getElementById('stat-active-days').innerText = data.days_active || 0;
        document.getElementById('stat-streak').innerText = data.streak_days || 0;

        const moodResponse = await fetch('/api/analytics/mood-trend');
        const moodData = await moodResponse.json();
        if (moodData.data && moodData.data.length > 0) {
            const avg = moodData.data.reduce((acc, curr) => acc + curr.avg_score, 0) / moodData.data.length;
            document.getElementById('stat-mood-score').innerText = avg.toFixed(1);
        }
    } catch (error) {
        console.error('Error fetching stats:', error);
    }
}

async function loadMoodTrends(ctx) {
    try {
        const response = await fetch('/api/analytics/mood-trend?days=365');
        const data = await response.json();
        if (!data.data || data.data.length === 0) return;

        const colors = getThemeColors();
        const labels = data.data.map(d => d.date);
        const scores = data.data.map(d => d.avg_score);

        if (charts.mood) charts.mood.destroy();
        charts.mood = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Sentiment Score',
                    data: scores,
                    borderColor: colors.accent,
                    backgroundColor: colors.accentBg,
                    fill: true,
                    tension: 0.4,
                    borderWidth: 3,
                    pointRadius: 4,
                    pointBackgroundColor: colors.accent
                }]
            },
            options: getChartOptions()
        });
    } catch (error) {
        console.error('Error loading mood trends:', error);
    }
}

async function loadAssessmentTrends(ctx) {
    try {
        const [phq9Res, gad7Res] = await Promise.all([
            fetch('/api/analytics/trends/phq9'),
            fetch('/api/analytics/trends/gad7')
        ]);
        const phq9Data = await phq9Res.json();
        const gad7Data = await gad7Res.json();

        const datasets = [];
        let labels = [];

        if (phq9Data.data && phq9Data.data.length > 0) {
            labels = phq9Data.data.map(d => new Date(d.date).toLocaleDateString());
            datasets.push({
                label: 'PHQ-9 (Depression)',
                data: phq9Data.data.map(d => d.score),
                borderColor: '#ef4444',
                tension: 0.3
            });
        }

        if (gad7Data.data && gad7Data.data.length > 0) {
            if (labels.length === 0) labels = gad7Data.data.map(d => new Date(d.date).toLocaleDateString());
            datasets.push({
                label: 'GAD-7 (Anxiety)',
                data: gad7Data.data.map(d => d.score),
                borderColor: '#3b82f6',
                tension: 0.3
            });
        }

        if (charts.assessment) charts.assessment.destroy();
        charts.assessment = new Chart(ctx, {
            type: 'line',
            data: { labels, datasets },
            options: getChartOptions()
        });
    } catch (error) {
        console.error('Error loading assessments:', error);
    }
}

async function loadCrisisPatterns(ctx) {
    try {
        const response = await fetch('/api/analytics/crisis-patterns');
        const data = await response.json();
        if (!data.severity_distribution || Object.keys(data.severity_distribution).length === 0) return;

        const labels = Object.keys(data.severity_distribution);
        const values = Object.values(data.severity_distribution);

        if (charts.crisis) charts.crisis.destroy();
        charts.crisis = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: labels,
                datasets: [{
                    data: values,
                    backgroundColor: ['#ef4444', '#f59e0b', '#3b82f6', '#10b981'],
                    borderWidth: 0
                }]
            },
            options: {
                ...getChartOptions(),
                plugins: {
                    ...getChartOptions().plugins,
                    legend: { position: 'bottom', labels: { color: getThemeColors().text } }
                }
            }
        });
    } catch (error) {
        console.error('Error loading crisis patterns:', error);
    }
}

async function loadEngagementMetrics(ctx) {
    try {
        const response = await fetch('/api/analytics/engagement');
        const data = await response.json();
        if (!data.daily_activity || data.daily_activity.length === 0) return;

        const colors = getThemeColors();
        if (charts.activity) charts.activity.destroy();
        charts.activity = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: data.daily_activity.map(d => d.date),
                datasets: [{
                    label: 'Messages per Day',
                    data: data.daily_activity.map(d => d.messages),
                    backgroundColor: colors.accent,
                    borderRadius: 8
                }]
            },
            options: getChartOptions()
        });
    } catch (error) {
        console.error('Error loading engagement:', error);
    }
}
