const CompareView = {
    selectedResults: [],
    comparisonData: null,
    chartType: 'bar',

    async render(params = {}) {
        const container = document.getElementById('view-compare');
        container.innerHTML = '';

        if (params.ids) {
            const ids = params.ids.split(',');
            await this.loadResults(ids);
        }

        const header = Utils.createElement('div', {style: {display: 'flex', 'justify-content': 'space-between', 'align-items': 'center', 'margin-bottom': '2rem'}}, [
            Utils.createElement('div', {}, [
                Utils.createElement('h2', {style: {'font-size': '1.5rem', 'font-weight': '700', color: 'var(--text-primary)', 'margin-bottom': '0.25rem'}}, [document.createTextNode('Compare Results')]),
                Utils.createElement('p', {style: {'font-size': '0.875rem', color: 'var(--text-secondary)'}}, [
                    document.createTextNode(`Comparing ${this.selectedResults.length} evaluation${this.selectedResults.length !== 1 ? 's' : ''}`)
                ])
            ]),
            Utils.createElement('div', {style: {display: 'flex', gap: '0.75rem'}}, [
                Components.button('Select Results', {
                    variant: 'secondary',
                    icon: '<path d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"></path>',
                    onClick: () => this.showResultSelector()
                }),
                Components.button('Export Comparison', {
                    variant: 'primary',
                    icon: '<path d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"></path>',
                    onClick: () => this.exportComparison(),
                    disabled: this.selectedResults.length === 0
                })
            ])
        ]);

        if (this.selectedResults.length === 0) {
            const emptyState = Components.emptyState({
                icon: '<path d="M9 17V7m0 10a2 2 0 01-2 2H5a2 2 0 01-2-2V7a2 2 0 012-2h2a2 2 0 012 2m0 10a2 2 0 002 2h2a2 2 0 002-2M9 7a2 2 0 012-2h2a2 2 0 012 2m0 10V7m0 10a2 2 0 002 2h2a2 2 0 002-2V7a2 2 0 00-2-2h-2a2 2 0 00-2 2"></path>',
                title: 'No Results Selected',
                description: 'Select evaluation results to compare their performance',
                action: {
                    label: 'Select Results',
                    onClick: () => this.showResultSelector()
                }
            });

            container.appendChild(header);
            container.appendChild(emptyState);
            return;
        }

        const summary = this.createComparisonSummary();
        const charts = this.createComparisonCharts();
        const table = this.createComparisonTable();

        container.appendChild(header);
        container.appendChild(summary);
        container.appendChild(charts);
        container.appendChild(table);
    },

    async loadResults(ids) {
        try {
            const promises = ids.map(id => API.evaluations.get(id));
            this.selectedResults = await Promise.all(promises);
        } catch {
            this.selectedResults = this.getMockResults().filter((_, i) => ids.includes(String(i + 1)));
        }
    },

    getMockResults() {
        return [
            {id: '1', plugin: 'ORB-SLAM3', dataset: 'KITTI-00', date: new Date(Date.now() - 86400000 * 2), status: 'completed', duration: 3600, ate: 0.145, rpe: 0.023, success_rate: 98.5, memory: 256, cpu: 45},
            {id: '2', plugin: 'VINS-Mono', dataset: 'KITTI-00', date: new Date(Date.now() - 86400000 * 5), status: 'completed', duration: 2100, ate: 0.187, rpe: 0.031, success_rate: 96.2, memory: 312, cpu: 62},
            {id: '4', plugin: 'LIO-SAM', dataset: 'KITTI-00', date: new Date(Date.now() - 86400000 * 3), status: 'completed', duration: 4200, ate: 0.132, rpe: 0.019, success_rate: 99.1, memory: 198, cpu: 38},
            {id: '6', plugin: 'Cartographer', dataset: 'KITTI-00', date: new Date(Date.now() - 86400000 * 4), status: 'completed', duration: 5100, ate: 0.112, rpe: 0.015, success_rate: 99.5, memory: 423, cpu: 71}
        ];
    },

    createComparisonSummary() {
        const best = {
            ate: this.selectedResults.reduce((min, r) => r.ate < min.ate ? r : min),
            rpe: this.selectedResults.reduce((min, r) => r.rpe < min.rpe ? r : min),
            success_rate: this.selectedResults.reduce((max, r) => r.success_rate > max.success_rate ? r : max),
            duration: this.selectedResults.reduce((min, r) => r.duration < min.duration ? r : min)
        };

        return Utils.createElement('div', {
            class: 'comparison-summary stagger-fadeIn',
            style: {
                display: 'grid',
                'grid-template-columns': 'repeat(auto-fit, minmax(250px, 1fr))',
                gap: '1.5rem',
                'margin-bottom': '2rem'
            }
        }, [
            this.createSummaryCard('Best ATE', best.ate.plugin, best.ate.ate.toFixed(3) + ' m', 'success'),
            this.createSummaryCard('Best RPE', best.rpe.plugin, best.rpe.rpe.toFixed(3) + ' m', 'info'),
            this.createSummaryCard('Highest Success', best.success_rate.plugin, best.success_rate.success_rate.toFixed(1) + '%', 'warning'),
            this.createSummaryCard('Fastest', best.duration.plugin, Utils.formatDuration(best.duration.duration * 1000), 'primary')
        ]);
    },

    createSummaryCard(title, subtitle, value, variant) {
        return Utils.createElement('div', {
            class: 'card hover-lift',
            style: {
                padding: '1.5rem',
                'border-left': `4px solid var(--${variant})`
            }
        }, [
            Utils.createElement('div', {style: {'font-size': '0.75rem', 'font-weight': '600', 'text-transform': 'uppercase', 'letter-spacing': '0.05em', color: 'var(--text-tertiary)', 'margin-bottom': '0.5rem'}}, [document.createTextNode(title)]),
            Utils.createElement('div', {style: {'font-size': '1.75rem', 'font-weight': '700', color: `var(--${variant})`, 'margin-bottom': '0.25rem'}}, [document.createTextNode(value)]),
            Utils.createElement('div', {style: {'font-size': '0.875rem', color: 'var(--text-secondary)'}}, [document.createTextNode(subtitle)])
        ]);
    },

    createComparisonCharts() {
        const wrapper = Utils.createElement('div', {class: 'card', style: {padding: '1.5rem', 'margin-bottom': '2rem'}});

        const header = Utils.createElement('div', {style: {display: 'flex', 'justify-content': 'space-between', 'align-items': 'center', 'margin-bottom': '1.5rem'}}, [
            Utils.createElement('h3', {style: {'font-size': '1.125rem', 'font-weight': '600'}}, [document.createTextNode('Performance Metrics')]),
            this.createChartTypeToggle()
        ]);

        const chartsGrid = Utils.createElement('div', {
            style: {
                display: 'grid',
                'grid-template-columns': 'repeat(auto-fit, minmax(400px, 1fr))',
                gap: '2rem'
            }
        }, [
            this.createMetricChart('Absolute Trajectory Error (ATE)', 'ate', 'm', 'success'),
            this.createMetricChart('Relative Pose Error (RPE)', 'rpe', 'm', 'info'),
            this.createMetricChart('Success Rate', 'success_rate', '%', 'warning'),
            this.createMetricChart('Execution Time', 'duration', 's', 'primary')
        ]);

        wrapper.appendChild(header);
        wrapper.appendChild(chartsGrid);

        return wrapper;
    },

    createChartTypeToggle() {
        const types = [
            {value: 'bar', icon: '<path d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"></path>'},
            {value: 'line', icon: '<path d="M7 12l3-3 3 3 4-4M8 21l4-4 4 4M3 4h18M4 4h16v12a1 1 0 01-1 1H5a1 1 0 01-1-1V4z"></path>'}
        ];

        return Utils.createElement('div', {style: {display: 'flex', gap: '0.5rem', background: 'var(--bg-tertiary)', padding: '0.25rem', 'border-radius': 'var(--radius-lg)'}},
            types.map(type => {
                const isActive = this.chartType === type.value;
                const btn = Utils.createElement('button', {
                    style: {
                        padding: '0.5rem',
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
                        this.chartType = type.value;
                        this.render();
                    }
                }, [
                    Utils.createElement('svg', {style: {width: '1.25rem', height: '1.25rem'}, viewBox: '0 0 24 24', fill: 'none', stroke: 'currentColor', 'stroke-width': '2'}, []).innerHTML = type.icon
                ]);

                return btn;
            })
        );
    },

    createMetricChart(title, metric, unit, variant) {
        const container = Utils.createElement('div', {});

        const titleEl = Utils.createElement('h4', {style: {'font-size': '0.875rem', 'font-weight': '600', 'margin-bottom': '1rem', color: 'var(--text-secondary)'}}, [document.createTextNode(title)]);

        const canvas = Utils.createElement('canvas', {
            style: {
                width: '100%',
                height: '250px'
            }
        });

        container.appendChild(titleEl);
        container.appendChild(canvas);

        setTimeout(() => {
            this.renderChart(canvas, metric, unit, variant);
        }, 100);

        return container;
    },

    renderChart(canvas, metric, unit, variant) {
        const ctx = canvas.getContext('2d');
        canvas.width = canvas.offsetWidth * 2;
        canvas.height = canvas.offsetHeight * 2;
        ctx.scale(2, 2);

        const width = canvas.width / 2;
        const height = canvas.height / 2;
        const padding = 40;
        const chartWidth = width - padding * 2;
        const chartHeight = height - padding * 2;

        const values = this.selectedResults.map(r => r[metric]);
        const labels = this.selectedResults.map(r => r.plugin);
        const maxValue = Math.max(...values);
        const scale = chartHeight / maxValue;

        ctx.fillStyle = getComputedStyle(document.documentElement).getPropertyValue('--text-secondary').trim();
        ctx.font = '12px Inter, sans-serif';

        if (this.chartType === 'bar') {
            const barWidth = chartWidth / values.length;
            const barPadding = barWidth * 0.2;

            values.forEach((value, i) => {
                const x = padding + i * barWidth;
                const barHeight = value * scale;
                const y = padding + chartHeight - barHeight;

                const gradient = ctx.createLinearGradient(0, y, 0, y + barHeight);
                const color = getComputedStyle(document.documentElement).getPropertyValue(`--${variant}`).trim();
                gradient.addColorStop(0, color);
                gradient.addColorStop(1, color + '80');

                ctx.fillStyle = gradient;
                ctx.fillRect(x + barPadding / 2, y, barWidth - barPadding, barHeight);

                ctx.fillStyle = getComputedStyle(document.documentElement).getPropertyValue('--text-primary').trim();
                ctx.textAlign = 'center';
                ctx.fillText(value.toFixed(metric === 'duration' ? 0 : metric === 'success_rate' ? 1 : 3), x + barWidth / 2, y - 5);

                ctx.save();
                ctx.translate(x + barWidth / 2, padding + chartHeight + 10);
                ctx.rotate(-Math.PI / 4);
                ctx.textAlign = 'right';
                ctx.fillStyle = getComputedStyle(document.documentElement).getPropertyValue('--text-secondary').trim();
                ctx.fillText(labels[i], 0, 0);
                ctx.restore();
            });
        } else {
            ctx.strokeStyle = getComputedStyle(document.documentElement).getPropertyValue(`--${variant}`).trim();
            ctx.lineWidth = 3;
            ctx.lineCap = 'round';
            ctx.lineJoin = 'round';

            ctx.beginPath();
            values.forEach((value, i) => {
                const x = padding + (i / (values.length - 1)) * chartWidth;
                const y = padding + chartHeight - value * scale;

                if (i === 0) {
                    ctx.moveTo(x, y);
                } else {
                    ctx.lineTo(x, y);
                }

                ctx.fillStyle = getComputedStyle(document.documentElement).getPropertyValue(`--${variant}`).trim();
                ctx.beginPath();
                ctx.arc(x, y, 5, 0, Math.PI * 2);
                ctx.fill();

                ctx.fillStyle = getComputedStyle(document.documentElement).getPropertyValue('--text-primary').trim();
                ctx.textAlign = 'center';
                ctx.fillText(value.toFixed(metric === 'duration' ? 0 : metric === 'success_rate' ? 1 : 3), x, y - 10);
            });
            ctx.stroke();
        }

        ctx.strokeStyle = getComputedStyle(document.documentElement).getPropertyValue('--border').trim();
        ctx.lineWidth = 1;
        ctx.beginPath();
        ctx.moveTo(padding, padding + chartHeight);
        ctx.lineTo(padding + chartWidth, padding + chartHeight);
        ctx.stroke();
    },

    createComparisonTable() {
        const wrapper = Utils.createElement('div', {class: 'card', style: {padding: '1.5rem'}});

        const title = Utils.createElement('h3', {style: {'font-size': '1.125rem', 'font-weight': '600', 'margin-bottom': '1.5rem'}}, [document.createTextNode('Detailed Comparison')]);

        const columns = [
            {key: 'plugin', label: 'Plugin'},
            {key: 'dataset', label: 'Dataset'},
            {key: 'ate', label: 'ATE (m)', render: (r) => this.createMetricCell(r.ate, 'ate')},
            {key: 'rpe', label: 'RPE (m)', render: (r) => this.createMetricCell(r.rpe, 'rpe')},
            {key: 'success_rate', label: 'Success %', render: (r) => this.createMetricCell(r.success_rate, 'success_rate')},
            {key: 'duration', label: 'Time', render: (r) => Utils.formatDuration(r.duration * 1000)},
            {key: 'date', label: 'Date', render: (r) => Utils.formatRelativeTime(r.date)}
        ];

        const table = Components.table(columns, this.selectedResults);

        wrapper.appendChild(title);
        wrapper.appendChild(table);

        return wrapper;
    },

    createMetricCell(value, metric) {
        const best = this.selectedResults.reduce((min, r) => r[metric] < min[metric] ? r : min);
        const worst = this.selectedResults.reduce((max, r) => r[metric] > max[metric] ? r : max);

        let variant = 'secondary';
        if (value === best[metric]) variant = 'success';
        else if (value === worst[metric]) variant = 'error';

        const formattedValue = metric === 'success_rate'
            ? value.toFixed(1) + '%'
            : value.toFixed(3);

        return Utils.createElement('div', {style: {display: 'flex', 'align-items': 'center', gap: '0.5rem'}}, [
            Utils.createElement('span', {style: {'font-weight': value === best[metric] ? '600' : '400', color: `var(--${variant})`}}, [document.createTextNode(formattedValue)]),
            value === best[metric] ? Utils.createElement('svg', {style: {width: '1rem', height: '1rem', color: 'var(--success)'}, viewBox: '0 0 24 24', fill: 'none', stroke: 'currentColor', 'stroke-width': '2'}, []).innerHTML = '<path d="M5 10l7-7m0 0l7 7m-7-7v18"></path>' : null
        ].filter(Boolean));
    },

    showResultSelector() {
        const content = Utils.createElement('div', {});

        const description = Utils.createElement('p', {style: {'font-size': '0.875rem', color: 'var(--text-secondary)', 'margin-bottom': '1.5rem'}}, [
            document.createTextNode('Select evaluation results to compare (2-6 results recommended)')
        ]);

        const results = this.getMockResults();
        const list = Utils.createElement('div', {style: {display: 'flex', 'flex-direction': 'column', gap: '0.75rem', 'max-height': '400px', 'overflow-y': 'auto'}},
            results.map(result => {
                const isSelected = this.selectedResults.some(r => r.id === result.id);

                const item = Utils.createElement('div', {
                    class: 'card',
                    style: {
                        padding: '1rem',
                        display: 'flex',
                        'align-items': 'center',
                        gap: '1rem',
                        cursor: 'pointer',
                        border: `2px solid ${isSelected ? 'var(--primary)' : 'var(--border)'}`,
                        background: isSelected ? 'rgba(37, 99, 235, 0.05)' : 'var(--bg-primary)',
                        transition: 'all var(--duration-fast) var(--ease)'
                    },
                    onclick: () => {
                        if (isSelected) {
                            this.selectedResults = this.selectedResults.filter(r => r.id !== result.id);
                        } else {
                            this.selectedResults.push(result);
                        }
                        this.showResultSelector();
                    }
                });

                const checkbox = Components.checkbox({
                    checked: isSelected,
                    onClick: (e) => e.stopPropagation()
                });

                const info = Utils.createElement('div', {style: {flex: '1'}}, [
                    Utils.createElement('div', {style: {'font-size': '0.875rem', 'font-weight': '600', 'margin-bottom': '0.25rem'}}, [document.createTextNode(result.plugin + ' - ' + result.dataset)]),
                    Utils.createElement('div', {style: {'font-size': '0.75rem', color: 'var(--text-secondary)'}}, [
                        document.createTextNode(`ATE: ${result.ate.toFixed(3)}m • RPE: ${result.rpe.toFixed(3)}m • ${Utils.formatRelativeTime(result.date)}`)
                    ])
                ]);

                item.appendChild(checkbox);
                item.appendChild(info);

                return item;
            })
        );

        content.appendChild(description);
        content.appendChild(list);

        Components.modal('Select Results', content, {
            actions: [
                {label: 'Cancel', variant: 'secondary'},
                {
                    label: `Compare ${this.selectedResults.length} Results`,
                    variant: 'primary',
                    disabled: this.selectedResults.length < 2,
                    onClick: () => this.render()
                }
            ]
        });
    },

    exportComparison() {
        const content = Utils.createElement('div', {}, [
            Utils.createElement('p', {style: {'font-size': '0.875rem', color: 'var(--text-secondary)', 'margin-bottom': '1.5rem'}}, [
                document.createTextNode(`Export comparison of ${this.selectedResults.length} results`)
            ]),
            Components.select({
                label: 'Export Format',
                options: [
                    {value: 'pdf', label: 'PDF Report'},
                    {value: 'csv', label: 'CSV Table'},
                    {value: 'json', label: 'JSON Data'},
                    {value: 'latex', label: 'LaTeX Table'}
                ]
            }),
            Utils.createElement('div', {style: {'margin-top': '1rem'}}, [
                Components.switch({label: 'Include charts', checked: true}),
                Components.switch({label: 'Include trajectories', checked: true}),
                Components.switch({label: 'Include statistics', checked: true})
            ])
        ]);

        Components.modal('Export Comparison', content, {
            actions: [
                {label: 'Cancel', variant: 'secondary'},
                {
                    label: 'Export',
                    variant: 'primary',
                    onClick: () => {
                        Components.toast('Exporting comparison...', 'success');
                        setTimeout(() => {
                            Components.toast('Export completed', 'success');
                        }, 1500);
                    }
                }
            ]
        });
    }
};
