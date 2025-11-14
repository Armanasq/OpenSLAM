const ResultsView = {
    results: [],
    sortBy: 'date',
    sortOrder: 'desc',
    filterStatus: 'all',
    selectedResults: new Set(),
    currentView: 'table',

    async render() {
        const container = document.getElementById('view-results');
        container.innerHTML = '';

        await this.loadResults();

        const header = Utils.createElement('div', {style: {display: 'flex', 'justify-content': 'space-between', 'align-items': 'center', 'margin-bottom': '2rem'}}, [
            Utils.createElement('div', {}, [
                Utils.createElement('h2', {style: {'font-size': '1.5rem', 'font-weight': '700', color: 'var(--text-primary)', 'margin-bottom': '0.25rem'}}, [document.createTextNode('Evaluation Results')]),
                Utils.createElement('p', {style: {'font-size': '0.875rem', color: 'var(--text-secondary)'}}, [document.createTextNode(`${this.results.length} evaluations • ${this.selectedResults.size} selected`)])
            ]),
            Utils.createElement('div', {style: {display: 'flex', gap: '0.75rem'}}, [
                this.selectedResults.size > 1 ? Components.button('Compare Selected', {
                    variant: 'secondary',
                    icon: '<path d="M9 17V7m0 10a2 2 0 01-2 2H5a2 2 0 01-2-2V7a2 2 0 012-2h2a2 2 0 012 2m0 10a2 2 0 002 2h2a2 2 0 002-2M9 7a2 2 0 012-2h2a2 2 0 012 2m0 10V7m0 10a2 2 0 002 2h2a2 2 0 002-2V7a2 2 0 00-2-2h-2a2 2 0 00-2 2"></path>',
                    onClick: () => this.compareSelected()
                }) : null,
                Components.button('Export', {
                    variant: 'secondary',
                    icon: '<path d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"></path>',
                    onClick: () => this.showExportModal()
                }),
                this.createViewToggle()
            ].filter(Boolean))
        ]);

        const toolbar = Utils.createElement('div', {style: {display: 'flex', gap: '1rem', 'margin-bottom': '1.5rem', 'flex-wrap': 'wrap', 'align-items': 'center'}}, [
            this.createFilterButtons(),
            Utils.createElement('div', {style: {flex: '1'}}),
            this.createSortDropdown()
        ]);

        const content = this.currentView === 'table'
            ? this.renderTableView()
            : this.renderCardView();

        container.appendChild(header);
        container.appendChild(toolbar);
        container.appendChild(content);
    },

    async loadResults() {
        try {
            const data = await API.evaluations.list();
            this.results = data.results || this.getMockResults();
        } catch {
            this.results = this.getMockResults();
        }
    },

    getMockResults() {
        return [
            {id: '1', plugin: 'ORB-SLAM3', dataset: 'KITTI-00', date: new Date(Date.now() - 86400000 * 2), status: 'completed', duration: 3600, ate: 0.145, rpe: 0.023, success_rate: 98.5},
            {id: '2', plugin: 'VINS-Mono', dataset: 'EuRoC MH-01', date: new Date(Date.now() - 86400000 * 5), status: 'completed', duration: 2100, ate: 0.187, rpe: 0.031, success_rate: 96.2},
            {id: '3', plugin: 'DSO', dataset: 'TUM RGB-D', date: new Date(Date.now() - 86400000 * 1), status: 'failed', duration: 450, ate: null, rpe: null, success_rate: 0},
            {id: '4', plugin: 'LIO-SAM', dataset: 'KITTI-05', date: new Date(Date.now() - 86400000 * 3), status: 'completed', duration: 4200, ate: 0.132, rpe: 0.019, success_rate: 99.1},
            {id: '5', plugin: 'ORB-SLAM3', dataset: 'EuRoC V1-01', date: new Date(Date.now() - 86400000 * 7), status: 'completed', duration: 1800, ate: 0.156, rpe: 0.027, success_rate: 97.8},
            {id: '6', plugin: 'Cartographer', dataset: 'KITTI-07', date: new Date(Date.now() - 86400000 * 4), status: 'completed', duration: 5100, ate: 0.112, rpe: 0.015, success_rate: 99.5}
        ];
    },

    createViewToggle() {
        const toggle = Utils.createElement('div', {class: 'view-toggle', style: {display: 'flex', background: 'var(--bg-tertiary)', 'border-radius': 'var(--radius-lg)', padding: '0.25rem'}}, [
            this.createViewButton('table', '<path d="M3 10h18M3 14h18m-9-4v8m-7 0h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z"></path>'),
            this.createViewButton('cards', '<path d="M4 5a1 1 0 011-1h4a1 1 0 011 1v4a1 1 0 01-1 1H5a1 1 0 01-1-1V5zM14 5a1 1 0 011-1h4a1 1 0 011 1v4a1 1 0 01-1 1h-4a1 1 0 01-1-1V5zM4 15a1 1 0 011-1h4a1 1 0 011 1v4a1 1 0 01-1 1H5a1 1 0 01-1-1v-4zM14 15a1 1 0 011-1h4a1 1 0 011 1v4a1 1 0 01-1 1h-4a1 1 0 01-1-1v-4z"></path>')
        ]);
        return toggle;
    },

    createViewButton(view, icon) {
        const isActive = this.currentView === view;
        const btn = Utils.createElement('button', {
            style: {
                padding: '0.5rem 0.75rem',
                border: 'none',
                background: isActive ? 'var(--bg-primary)' : 'transparent',
                color: isActive ? 'var(--primary)' : 'var(--text-secondary)',
                'border-radius': 'var(--radius-md)',
                cursor: 'pointer',
                display: 'flex',
                'align-items': 'center',
                'justify-content': 'center',
                transition: 'all var(--duration-fast) var(--ease)',
                'box-shadow': isActive ? 'var(--shadow-sm)' : 'none'
            },
            onclick: () => {
                this.currentView = view;
                this.render();
            }
        }, [
            Utils.createElement('svg', {style: {width: '1.25rem', height: '1.25rem'}, viewBox: '0 0 24 24', fill: 'none', stroke: 'currentColor', 'stroke-width': '2'}, []).innerHTML = icon
        ]);

        return btn;
    },

    createFilterButtons() {
        const filters = [
            {value: 'all', label: 'All', count: this.results.length},
            {value: 'completed', label: 'Completed', count: this.results.filter(r => r.status === 'completed').length},
            {value: 'failed', label: 'Failed', count: this.results.filter(r => r.status === 'failed').length}
        ];

        return Utils.createElement('div', {style: {display: 'flex', gap: '0.5rem'}},
            filters.map(filter => {
                const isActive = this.filterStatus === filter.value;
                const btn = Utils.createElement('button', {
                    style: {
                        padding: '0.5rem 1rem',
                        border: `1px solid ${isActive ? 'var(--primary)' : 'var(--border)'}`,
                        background: isActive ? 'rgba(37, 99, 235, 0.1)' : 'var(--bg-primary)',
                        color: isActive ? 'var(--primary)' : 'var(--text-secondary)',
                        'border-radius': 'var(--radius-lg)',
                        cursor: 'pointer',
                        'font-size': '0.875rem',
                        'font-weight': '500',
                        display: 'flex',
                        'align-items': 'center',
                        gap: '0.5rem',
                        transition: 'all var(--duration-fast) var(--ease)'
                    },
                    onclick: () => {
                        this.filterStatus = filter.value;
                        this.render();
                    }
                }, [
                    document.createTextNode(filter.label),
                    Components.badge(filter.count.toString(), isActive ? 'primary' : 'secondary')
                ]);

                btn.addEventListener('mouseenter', () => {
                    if (!isActive) {
                        btn.style.borderColor = 'var(--primary-light)';
                        btn.style.transform = 'translateY(-2px)';
                    }
                });

                btn.addEventListener('mouseleave', () => {
                    if (!isActive) {
                        btn.style.borderColor = 'var(--border)';
                        btn.style.transform = 'translateY(0)';
                    }
                });

                return btn;
            })
        );
    },

    createSortDropdown() {
        const options = [
            {value: 'date', label: 'Sort by Date'},
            {value: 'plugin', label: 'Sort by Plugin'},
            {value: 'dataset', label: 'Sort by Dataset'},
            {value: 'ate', label: 'Sort by ATE'},
            {value: 'rpe', label: 'Sort by RPE'},
            {value: 'duration', label: 'Sort by Duration'}
        ];

        return Components.select({
            options: options,
            value: this.sortBy,
            onChange: (value) => {
                this.sortBy = value;
                this.render();
            },
            style: {'min-width': '180px'}
        });
    },

    getFilteredAndSortedResults() {
        let filtered = this.results;

        if (this.filterStatus !== 'all') {
            filtered = filtered.filter(r => r.status === this.filterStatus);
        }

        filtered.sort((a, b) => {
            let aVal, bVal;

            switch (this.sortBy) {
                case 'date':
                    aVal = a.date;
                    bVal = b.date;
                    break;
                case 'plugin':
                    aVal = a.plugin;
                    bVal = b.plugin;
                    break;
                case 'dataset':
                    aVal = a.dataset;
                    bVal = b.dataset;
                    break;
                case 'ate':
                    aVal = a.ate || Infinity;
                    bVal = b.ate || Infinity;
                    break;
                case 'rpe':
                    aVal = a.rpe || Infinity;
                    bVal = b.rpe || Infinity;
                    break;
                case 'duration':
                    aVal = a.duration;
                    bVal = b.duration;
                    break;
                default:
                    return 0;
            }

            if (this.sortOrder === 'asc') {
                return aVal > bVal ? 1 : -1;
            } else {
                return aVal < bVal ? 1 : -1;
            }
        });

        return filtered;
    },

    renderTableView() {
        const results = this.getFilteredAndSortedResults();

        if (results.length === 0) {
            return Components.emptyState({
                icon: '<path d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"></path>',
                title: 'No Results Found',
                description: 'Try adjusting your filters or run a new evaluation'
            });
        }

        const columns = [
            {key: 'select', label: '', width: '40px', render: (result) => this.renderCheckbox(result)},
            {key: 'status', label: 'Status', width: '100px', render: (result) => Components.badge(result.status, result.status === 'completed' ? 'success' : 'error')},
            {key: 'plugin', label: 'Plugin', sortable: true},
            {key: 'dataset', label: 'Dataset', sortable: true},
            {key: 'ate', label: 'ATE (m)', sortable: true, render: (result) => result.ate ? result.ate.toFixed(3) : 'N/A'},
            {key: 'rpe', label: 'RPE (m)', sortable: true, render: (result) => result.rpe ? result.rpe.toFixed(3) : 'N/A'},
            {key: 'success_rate', label: 'Success %', sortable: true, render: (result) => result.success_rate ? result.success_rate.toFixed(1) + '%' : 'N/A'},
            {key: 'duration', label: 'Duration', sortable: true, render: (result) => Utils.formatDuration(result.duration * 1000)},
            {key: 'date', label: 'Date', sortable: true, render: (result) => Utils.formatRelativeTime(result.date)},
            {key: 'actions', label: 'Actions', width: '120px', render: (result) => this.renderActions(result)}
        ];

        return Components.table(columns, results, {
            onRowClick: (result) => this.showResultDetails(result),
            onSort: (key, order) => {
                this.sortBy = key;
                this.sortOrder = order;
                this.render();
            },
            currentSort: {key: this.sortBy, order: this.sortOrder}
        });
    },

    renderCardView() {
        const results = this.getFilteredAndSortedResults();

        if (results.length === 0) {
            return Components.emptyState({
                icon: '<path d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"></path>',
                title: 'No Results Found',
                description: 'Try adjusting your filters or run a new evaluation'
            });
        }

        return Utils.createElement('div', {
            class: 'stagger-fadeIn',
            style: {
                display: 'grid',
                'grid-template-columns': 'repeat(auto-fill, minmax(350px, 1fr))',
                gap: '1.5rem'
            }
        }, results.map((result, index) => this.createResultCard(result, index)));
    },

    createResultCard(result, index) {
        const isSelected = this.selectedResults.has(result.id);

        const card = Utils.createElement('div', {
            class: 'result-card card hover-lift',
            style: {
                padding: '1.5rem',
                cursor: 'pointer',
                position: 'relative',
                border: `2px solid ${isSelected ? 'var(--primary)' : 'var(--border)'}`,
                'animation-delay': `${index * 50}ms`
            },
            onclick: () => this.showResultDetails(result)
        });

        const checkbox = this.renderCheckbox(result);
        checkbox.style.position = 'absolute';
        checkbox.style.top = '1rem';
        checkbox.style.right = '1rem';

        const statusBadge = Utils.createElement('div', {style: {'margin-bottom': '1rem'}},
            [Components.badge(result.status, result.status === 'completed' ? 'success' : 'error')]
        );

        const header = Utils.createElement('div', {style: {'margin-bottom': '1rem'}}, [
            Utils.createElement('h3', {style: {'font-size': '1.125rem', 'font-weight': '600', 'margin-bottom': '0.25rem'}}, [document.createTextNode(result.plugin)]),
            Utils.createElement('div', {style: {'font-size': '0.875rem', color: 'var(--text-secondary)'}}, [document.createTextNode(result.dataset)])
        ]);

        const metrics = result.status === 'completed' ? Utils.createElement('div', {style: {display: 'grid', 'grid-template-columns': 'repeat(2, 1fr)', gap: '1rem', 'margin-bottom': '1rem'}}, [
            this.createMetricItem('ATE', result.ate.toFixed(3) + ' m', 'success'),
            this.createMetricItem('RPE', result.rpe.toFixed(3) + ' m', 'info'),
            this.createMetricItem('Success Rate', result.success_rate.toFixed(1) + '%', 'warning'),
            this.createMetricItem('Duration', Utils.formatDuration(result.duration * 1000), 'secondary')
        ]) : Utils.createElement('div', {style: {'margin-bottom': '1rem'}}, [
            Utils.createElement('p', {style: {'font-size': '0.875rem', color: 'var(--text-secondary)', 'text-align': 'center', padding: '1rem', background: 'var(--bg-tertiary)', 'border-radius': 'var(--radius-lg)'}}, [document.createTextNode('Evaluation failed - no metrics available')])
        ]);

        const footer = Utils.createElement('div', {style: {display: 'flex', 'justify-content': 'space-between', 'align-items': 'center', 'padding-top': '1rem', 'border-top': '1px solid var(--border)'}}, [
            Utils.createElement('div', {style: {'font-size': '0.75rem', color: 'var(--text-tertiary)'}}, [document.createTextNode(Utils.formatRelativeTime(result.date))]),
            Utils.createElement('div', {style: {display: 'flex', gap: '0.5rem'}},
                result.status === 'completed' ? [
                    this.createIconButton('<path d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"></path><path d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"></path>', 'View Details', (e) => {e.stopPropagation(); this.showResultDetails(result);}),
                    this.createIconButton('<path d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"></path>', 'Export', (e) => {e.stopPropagation(); this.exportResult(result);})
                ] : []
            )
        ]);

        card.appendChild(checkbox);
        card.appendChild(statusBadge);
        card.appendChild(header);
        card.appendChild(metrics);
        card.appendChild(footer);

        return card;
    },

    createMetricItem(label, value, variant) {
        return Utils.createElement('div', {style: {padding: '0.75rem', background: 'var(--bg-tertiary)', 'border-radius': 'var(--radius-lg)', 'text-align': 'center'}}, [
            Utils.createElement('div', {style: {'font-size': '1rem', 'font-weight': '600', color: `var(--${variant})`, 'margin-bottom': '0.25rem'}}, [document.createTextNode(value)]),
            Utils.createElement('div', {style: {'font-size': '0.75rem', color: 'var(--text-tertiary)'}}, [document.createTextNode(label)])
        ]);
    },

    renderCheckbox(result) {
        const isSelected = this.selectedResults.has(result.id);

        return Components.checkbox({
            checked: isSelected,
            onChange: (checked) => {
                if (checked) {
                    this.selectedResults.add(result.id);
                } else {
                    this.selectedResults.delete(result.id);
                }
                this.render();
            },
            onClick: (e) => e.stopPropagation()
        });
    },

    renderActions(result) {
        return Utils.createElement('div', {style: {display: 'flex', gap: '0.5rem', 'justify-content': 'flex-end'}}, [
            this.createIconButton('<path d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"></path><path d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"></path>', 'View', (e) => {e.stopPropagation(); this.showResultDetails(result);}),
            result.status === 'completed' ? this.createIconButton('<path d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"></path>', 'Export', (e) => {e.stopPropagation(); this.exportResult(result);}) : null
        ].filter(Boolean));
    },

    createIconButton(icon, tooltip, onClick) {
        const btn = Utils.createElement('button', {
            class: 'icon-button',
            style: {
                width: '2rem',
                height: '2rem',
                border: '1px solid var(--border)',
                background: 'var(--bg-primary)',
                'border-radius': 'var(--radius-md)',
                display: 'flex',
                'align-items': 'center',
                'justify-content': 'center',
                cursor: 'pointer',
                color: 'var(--text-secondary)',
                transition: 'all var(--duration-fast) var(--ease)'
            },
            onclick: onClick,
            title: tooltip
        }, [
            Utils.createElement('svg', {style: {width: '1rem', height: '1rem'}, viewBox: '0 0 24 24', fill: 'none', stroke: 'currentColor', 'stroke-width': '2'}, []).innerHTML = icon
        ]);

        btn.addEventListener('mouseenter', () => {
            btn.style.background = 'var(--primary)';
            btn.style.borderColor = 'var(--primary)';
            btn.style.color = 'var(--text-inverse)';
            btn.style.transform = 'scale(1.1)';
        });

        btn.addEventListener('mouseleave', () => {
            btn.style.background = 'var(--bg-primary)';
            btn.style.borderColor = 'var(--border)';
            btn.style.color = 'var(--text-secondary)';
            btn.style.transform = 'scale(1)';
        });

        return btn;
    },

    showResultDetails(result) {
        const content = Utils.createElement('div', {}, [
            Utils.createElement('div', {style: {display: 'grid', 'grid-template-columns': 'repeat(2, 1fr)', gap: '1.5rem', 'margin-bottom': '2rem'}}, [
                Utils.createElement('div', {}, [
                    Utils.createElement('h4', {style: {'font-size': '0.875rem', 'font-weight': '600', 'margin-bottom': '1rem', color: 'var(--text-secondary)', 'text-transform': 'uppercase', 'letter-spacing': '0.05em'}}, [document.createTextNode('Evaluation Details')]),
                    Utils.createElement('div', {style: {display: 'grid', gap: '0.75rem'}}, [
                        this.createDetailRow('Plugin', result.plugin),
                        this.createDetailRow('Dataset', result.dataset),
                        this.createDetailRow('Status', Components.badge(result.status, result.status === 'completed' ? 'success' : 'error')),
                        this.createDetailRow('Duration', Utils.formatDuration(result.duration * 1000)),
                        this.createDetailRow('Date', Utils.formatDateTime(result.date))
                    ])
                ]),
                result.status === 'completed' ? Utils.createElement('div', {}, [
                    Utils.createElement('h4', {style: {'font-size': '0.875rem', 'font-weight': '600', 'margin-bottom': '1rem', color: 'var(--text-secondary)', 'text-transform': 'uppercase', 'letter-spacing': '0.05em'}}, [document.createTextNode('Metrics')]),
                    Utils.createElement('div', {style: {display: 'grid', gap: '0.75rem'}}, [
                        this.createDetailRow('ATE', result.ate.toFixed(3) + ' m'),
                        this.createDetailRow('RPE', result.rpe.toFixed(3) + ' m'),
                        this.createDetailRow('Success Rate', result.success_rate.toFixed(1) + '%')
                    ])
                ]) : null
            ].filter(Boolean)),
            result.status === 'completed' ? Utils.createElement('div', {}, [
                Utils.createElement('h4', {style: {'font-size': '0.875rem', 'font-weight': '600', 'margin-bottom': '1rem', color: 'var(--text-secondary)', 'text-transform': 'uppercase', 'letter-spacing': '0.05em'}}, [document.createTextNode('Trajectory Visualization')]),
                this.createTrajectoryPlot(result)
            ]) : Utils.createElement('div', {class: 'card', style: {padding: '2rem', 'text-align': 'center', background: 'var(--bg-tertiary)'}}, [
                Utils.createElement('svg', {style: {width: '3rem', height: '3rem', color: 'var(--error)', margin: '0 auto 1rem'}, viewBox: '0 0 24 24', fill: 'none', stroke: 'currentColor', 'stroke-width': '2'}, []).innerHTML = '<path d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>',
                Utils.createElement('h4', {style: {'font-size': '1rem', 'font-weight': '600', 'margin-bottom': '0.5rem'}}, [document.createTextNode('Evaluation Failed')]),
                Utils.createElement('p', {style: {'font-size': '0.875rem', color: 'var(--text-secondary)'}}, [document.createTextNode('No visualization available for failed evaluations')])
            ])
        ]);

        Components.modal(result.plugin + ' - ' + result.dataset, content, {
            size: 'large',
            actions: result.status === 'completed' ? [
                {label: 'Export', variant: 'secondary', onClick: () => this.exportResult(result)},
                {label: 'Close', variant: 'primary'}
            ] : [{label: 'Close', variant: 'primary'}]
        });
    },

    createDetailRow(label, value) {
        return Utils.createElement('div', {style: {display: 'flex', 'justify-content': 'space-between', 'align-items': 'center'}}, [
            Utils.createElement('span', {style: {'font-size': '0.875rem', color: 'var(--text-secondary)'}}, [document.createTextNode(label)]),
            typeof value === 'string'
                ? Utils.createElement('span', {style: {'font-size': '0.875rem', 'font-weight': '600', color: 'var(--text-primary)'}}, [document.createTextNode(value)])
                : value
        ]);
    },

    createTrajectoryPlot(result) {
        const canvas = Utils.createElement('canvas', {
            style: {
                width: '100%',
                height: '400px',
                background: 'var(--bg-tertiary)',
                'border-radius': 'var(--radius-lg)',
                border: '1px solid var(--border)'
            }
        });

        setTimeout(() => {
            const ctx = canvas.getContext('2d');
            canvas.width = canvas.offsetWidth * 2;
            canvas.height = canvas.offsetHeight * 2;
            ctx.scale(2, 2);

            const width = canvas.width / 2;
            const height = canvas.height / 2;
            const centerX = width / 2;
            const centerY = height / 2;
            const scale = Math.min(width, height) * 0.3;

            ctx.strokeStyle = getComputedStyle(document.documentElement).getPropertyValue('--primary').trim();
            ctx.lineWidth = 2;
            ctx.lineCap = 'round';
            ctx.lineJoin = 'round';

            ctx.beginPath();
            for (let i = 0; i <= 100; i++) {
                const t = i / 100;
                const angle = t * Math.PI * 4;
                const radius = t * scale;
                const x = centerX + Math.cos(angle) * radius;
                const y = centerY + Math.sin(angle) * radius;

                if (i === 0) {
                    ctx.moveTo(x, y);
                } else {
                    ctx.lineTo(x, y);
                }
            }
            ctx.stroke();

            ctx.fillStyle = getComputedStyle(document.documentElement).getPropertyValue('--success').trim();
            ctx.beginPath();
            ctx.arc(centerX, centerY, 6, 0, Math.PI * 2);
            ctx.fill();

            const endAngle = Math.PI * 4;
            const endRadius = scale;
            const endX = centerX + Math.cos(endAngle) * endRadius;
            const endY = centerY + Math.sin(endAngle) * endRadius;

            ctx.fillStyle = getComputedStyle(document.documentElement).getPropertyValue('--error').trim();
            ctx.beginPath();
            ctx.arc(endX, endY, 6, 0, Math.PI * 2);
            ctx.fill();

            ctx.fillStyle = getComputedStyle(document.documentElement).getPropertyValue('--text-secondary').trim();
            ctx.font = '12px Inter, sans-serif';
            ctx.fillText('Start', centerX + 10, centerY);
            ctx.fillText('End', endX + 10, endY);
        }, 100);

        return canvas;
    },

    compareSelected() {
        const selectedIds = Array.from(this.selectedResults);
        App.navigate('compare', {ids: selectedIds.join(',')});
    },

    exportResult(result) {
        this.showExportModal([result.id]);
    },

    showExportModal(ids = null) {
        const exportIds = ids || Array.from(this.selectedResults);

        if (exportIds.length === 0) {
            Components.toast('Please select at least one result to export', 'warning');
            return;
        }

        const content = Utils.createElement('div', {}, [
            Utils.createElement('p', {style: {'font-size': '0.875rem', color: 'var(--text-secondary)', 'margin-bottom': '1.5rem'}}, [
                document.createTextNode(`Export ${exportIds.length} evaluation result${exportIds.length > 1 ? 's' : ''}`)
            ]),
            Components.select({
                label: 'Export Format',
                options: [
                    {value: 'json', label: 'JSON'},
                    {value: 'csv', label: 'CSV'},
                    {value: 'pdf', label: 'PDF Report'},
                    {value: 'latex', label: 'LaTeX Table'}
                ]
            }),
            Utils.createElement('div', {style: {'margin-top': '1rem'}}, [
                Components.switch({label: 'Include trajectory data', checked: true}),
                Components.switch({label: 'Include metrics plots', checked: true}),
                Components.switch({label: 'Include configuration', checked: false})
            ])
        ]);

        Components.modal('Export Results', content, {
            actions: [
                {label: 'Cancel', variant: 'secondary'},
                {
                    label: 'Export',
                    variant: 'primary',
                    onClick: () => {
                        Components.toast(`Exporting ${exportIds.length} result${exportIds.length > 1 ? 's' : ''}...`, 'success');
                        setTimeout(() => {
                            Components.toast('Export completed', 'success');
                        }, 1500);
                    }
                }
            ]
        });
    }
};
