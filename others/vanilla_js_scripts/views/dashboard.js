const DashboardView = {
    async render() {
        const container = document.getElementById('view-dashboard');
        container.innerHTML = '';

        const stats = await this.fetchStats();
        const recentActivity = await this.fetchRecentActivity();

        const statsGrid = Utils.createElement('div', {class: 'stats-grid', style: {display: 'grid', 'grid-template-columns': 'repeat(auto-fit, minmax(250px, 1fr))', gap: '1.5rem', 'margin-bottom': '2rem'}}, [
            this.createStatCard('Plugins', stats.plugins, 'success', '<path d="M12 2v4m0 12v4M4.93 4.93l2.83 2.83m8.48 8.48l2.83 2.83M2 12h4m12 0h4M4.93 19.07l2.83-2.83m8.48-8.48l2.83-2.83"></path>'),
            this.createStatCard('Datasets', stats.datasets, 'primary', '<path d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2z"></path>'),
            this.createStatCard('Evaluations', stats.evaluations, 'warning', '<path d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"></path>'),
            this.createStatCard('Success Rate', stats.successRate + '%', 'info', '<path d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path>')
        ]);

        const mainGrid = Utils.createElement('div', {style: {display: 'grid', 'grid-template-columns': '2fr 1fr', gap: '1.5rem', 'margin-bottom': '2rem'}}, [
            this.createQuickActions(),
            this.createSystemStatus()
        ]);

        const activityCard = Components.card({
            title: 'Recent Activity',
            subtitle: 'Latest evaluations and results',
            body: this.createActivityList(recentActivity)
        });

        container.appendChild(statsGrid);
        container.appendChild(mainGrid);
        container.appendChild(activityCard);

        this.startLiveUpdates();
    },

    createStatCard(label, value, variant, icon) {
        const card = Utils.createElement('div', {class: 'stat-card card hover-lift', style: {'padding': '1.5rem', 'border-left': `4px solid var(--${variant})`}}, [
            Utils.createElement('div', {style: {display: 'flex', 'justify-content': 'space-between', 'align-items': 'flex-start', 'margin-bottom': '0.5rem'}}, [
                Utils.createElement('div', {}, [
                    Utils.createElement('div', {style: {'font-size': '0.875rem', color: 'var(--text-secondary)', 'margin-bottom': '0.25rem'}}, [document.createTextNode(label)]),
                    Utils.createElement('div', {class: 'stat-value', style: {'font-size': '2rem', 'font-weight': '700', color: 'var(--text-primary)'}}, [document.createTextNode(value)])
                ]),
                Utils.createElement('div', {style: {width: '3rem', height: '3rem', 'border-radius': 'var(--radius-xl)', background: `rgba(var(--${variant}-rgb), 0.1)`, display: 'flex', 'align-items': 'center', 'justify-content': 'center'}}, [
                    Utils.createElement('svg', {style: {width: '1.5rem', height: '1.5rem', color: `var(--${variant})`}, viewBox: '0 0 24 24', fill: 'none', stroke: 'currentColor', 'stroke-width': '2'}, []).innerHTML = icon
                ])
            ]),
            Utils.createElement('div', {style: {'font-size': '0.75rem', color: 'var(--text-tertiary)', display: 'flex', 'align-items': 'center', gap: '0.25rem'}}, [
                Utils.createElement('svg', {style: {width: '1rem', height: '1rem', color: 'var(--success)'}, viewBox: '0 0 24 24', fill: 'none', stroke: 'currentColor', 'stroke-width': '2'}, []).innerHTML = '<path d="M5 10l7-7m0 0l7 7m-7-7v18"></path>',
                document.createTextNode('+12% from last month')
            ])
        ]);

        setTimeout(() => {
            const valueEl = card.querySelector('.stat-value');
            const targetValue = parseInt(value);
            Utils.animateValue(0, targetValue, 1000, v => valueEl.textContent = Math.floor(v));
        }, 100);

        return card;
    },

    createQuickActions() {
        return Components.card({
            title: 'Quick Actions',
            subtitle: 'Common tasks and workflows',
            body: Utils.createElement('div', {class: 'quick-actions', style: {display: 'grid', gap: '0.75rem'}}, [
                this.createQuickAction('Evaluate Plugin', '<path d="M13 10V3L4 14h7v7l9-11h-7z"></path>', () => App.navigate('evaluate')),
                this.createQuickAction('Upload Dataset', '<path d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"></path>', () => App.navigate('datasets')),
                this.createQuickAction('Compare Results', '<path d="M9 17V7m0 10a2 2 0 01-2 2H5a2 2 0 01-2-2V7a2 2 0 012-2h2a2 2 0 012 2m0 10a2 2 0 002 2h2a2 2 0 002-2M9 7a2 2 0 012-2h2a2 2 0 012 2m0 10V7m0 10a2 2 0 002 2h2a2 2 0 002-2V7a2 2 0 00-2-2h-2a2 2 0 00-2 2"></path>', () => App.navigate('compare')),
                this.createQuickAction('View Results', '<path d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"></path>', () => App.navigate('results'))
            ])
        });
    },

    createQuickAction(label, icon, action) {
        const btn = Utils.createElement('button', {class: 'quick-action-btn card', style: {display: 'flex', 'align-items': 'center', gap: '1rem', padding: '1rem', border: '1px solid var(--border)', background: 'var(--bg-primary)', cursor: 'pointer', transition: 'all var(--duration-fast) var(--ease)'}, onclick: action}, [
            Utils.createElement('div', {style: {width: '2.5rem', height: '2.5rem', 'border-radius': 'var(--radius-lg)', background: 'var(--bg-tertiary)', display: 'flex', 'align-items': 'center', 'justify-content': 'center', transition: 'all var(--duration-fast) var(--ease)'}}, [
                Utils.createElement('svg', {style: {width: '1.25rem', height: '1.25rem', color: 'var(--primary)'}, viewBox: '0 0 24 24', fill: 'none', stroke: 'currentColor', 'stroke-width': '2'}, []).innerHTML = icon
            ]),
            Utils.createElement('div', {style: {'font-size': '0.875rem', 'font-weight': '500', color: 'var(--text-primary)', flex: '1'}}, [document.createTextNode(label)]),
            Utils.createElement('svg', {style: {width: '1rem', height: '1rem', color: 'var(--text-tertiary)'}, viewBox: '0 0 24 24', fill: 'none', stroke: 'currentColor', 'stroke-width': '2'}, []).innerHTML = '<path d="M9 5l7 7-7 7"></path>'
        ]);

        btn.addEventListener('mouseenter', () => {
            btn.style.transform = 'translateX(4px)';
            btn.querySelector('div').style.background = 'var(--primary)';
            btn.querySelector('svg').style.color = 'var(--text-inverse)';
        });

        btn.addEventListener('mouseleave', () => {
            btn.style.transform = 'translateX(0)';
            btn.querySelector('div').style.background = 'var(--bg-tertiary)';
            btn.querySelector('svg').style.color = 'var(--primary)';
        });

        return btn;
    },

    createSystemStatus() {
        return Components.card({
            title: 'System Status',
            subtitle: 'Health and performance',
            body: Utils.createElement('div', {style: {display: 'flex', 'flex-direction': 'column', gap: '1rem'}}, [
                this.createStatusItem('CPU Usage', 45, 'success'),
                this.createStatusItem('Memory', 68, 'warning'),
                this.createStatusItem('Disk Space', 82, 'error'),
                this.createStatusItem('Active Jobs', 3, 'info')
            ])
        });
    },

    createStatusItem(label, value, variant) {
        return Utils.createElement('div', {}, [
            Utils.createElement('div', {style: {display: 'flex', 'justify-content': 'space-between', 'margin-bottom': '0.5rem'}}, [
                Utils.createElement('span', {style: {'font-size': '0.875rem', color: 'var(--text-secondary)'}}, [document.createTextNode(label)]),
                Utils.createElement('span', {style: {'font-size': '0.875rem', 'font-weight': '600', color: `var(--${variant})`}}, [document.createTextNode(typeof value === 'number' && value > 10 ? value + '%' : value)])
            ]),
            Components.progress(value, 100)
        ]);
    },

    createActivityList(activities) {
        if (!activities || activities.length === 0) {
            return Components.emptyState({
                icon: '<path d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"></path>',
                title: 'No Recent Activity',
                description: 'Start evaluating plugins to see activity here'
            });
        }

        return Utils.createElement('div', {class: 'activity-list stagger-fadeIn', style: {display: 'flex', 'flex-direction': 'column', gap: '0.75rem'}},
            activities.map(activity => this.createActivityItem(activity))
        );
    },

    createActivityItem(activity) {
        const {type, title, time, status} = activity;
        const icon = type === 'evaluation' ? '<path d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path>' : '<path d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"></path>';

        return Utils.createElement('div', {class: 'activity-item', style: {display: 'flex', 'align-items': 'center', gap: '1rem', padding: '1rem', 'border-radius': 'var(--radius-lg)', background: 'var(--bg-secondary)', transition: 'all var(--duration-fast) var(--ease)', cursor: 'pointer'}}, [
            Utils.createElement('div', {style: {width: '2.5rem', height: '2.5rem', 'border-radius': 'var(--radius-lg)', background: 'var(--bg-primary)', display: 'flex', 'align-items': 'center', 'justify-content': 'center'}}, [
                Utils.createElement('svg', {style: {width: '1.25rem', height: '1.25rem', color: 'var(--primary)'}, viewBox: '0 0 24 24', fill: 'none', stroke: 'currentColor', 'stroke-width': '2'}, []).innerHTML = icon
            ]),
            Utils.createElement('div', {style: {flex: '1'}}, [
                Utils.createElement('div', {style: {'font-size': '0.875rem', 'font-weight': '500', color: 'var(--text-primary)', 'margin-bottom': '0.25rem'}}, [document.createTextNode(title)]),
                Utils.createElement('div', {style: {'font-size': '0.75rem', color: 'var(--text-secondary)'}}, [document.createTextNode(Utils.formatRelativeTime(time))])
            ]),
            Components.badge(status, status === 'completed' ? 'success' : status === 'failed' ? 'error' : 'warning')
        ]);
    },

    async fetchStats() {
        try {
            const data = await API.system.status();
            return data.stats || {plugins: 6, datasets: 12, evaluations: 48, successRate: 94};
        } catch {
            return {plugins: 6, datasets: 12, evaluations: 48, successRate: 94};
        }
    },

    async fetchRecentActivity() {
        try {
            const data = await API.evaluations.list({limit: 5});
            return data.results || [];
        } catch {
            return [
                {type: 'evaluation', title: 'ORB-SLAM3 on KITTI-00', time: new Date(Date.now() - 3600000), status: 'completed'},
                {type: 'evaluation', title: 'VINS-Mono on EuRoC', time: new Date(Date.now() - 7200000), status: 'completed'},
                {type: 'evaluation', title: 'DSO on TUM RGB-D', time: new Date(Date.now() - 10800000), status: 'failed'},
                {type: 'result', title: 'Comparison Report Generated', time: new Date(Date.now() - 14400000), status: 'completed'},
                {type: 'dataset', title: 'KITTI-05 Uploaded', time: new Date(Date.now() - 18000000), status: 'completed'}
            ];
        }
    },

    startLiveUpdates() {
        WS.on('evaluation_complete', data => {
            Components.toast(`Evaluation ${data.name} completed`, 'success');
            this.render();
        });

        WS.on('evaluation_failed', data => {
            Components.toast(`Evaluation ${data.name} failed`, 'error');
            this.render();
        });
    }
};
