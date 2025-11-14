const BatchView = {
    batches: [],
    evaluationMatrix: [],

    async render() {
        const container = document.getElementById('view-batch');
        container.innerHTML = '';

        await this.loadBatches();

        const header = Utils.createElement('div', {style: {display: 'flex', 'justify-content': 'space-between', 'align-items': 'center', 'margin-bottom': '2rem'}}, [
            Utils.createElement('div', {}, [
                Utils.createElement('h2', {style: {'font-size': '1.5rem', 'font-weight': '700', color: 'var(--text-primary)', 'margin-bottom': '0.25rem'}}, [document.createTextNode('Batch Evaluations')]),
                Utils.createElement('p', {style: {'font-size': '0.875rem', color: 'var(--text-secondary)'}}, [document.createTextNode('Run multiple SLAM evaluations in parallel')])
            ]),
            Components.button('New Batch', {
                variant: 'primary',
                icon: '<path d="M12 4v16m8-8H4"></path>',
                onClick: () => this.createNewBatch()
            })
        ]);

        const tabs = this.createTabs();
        const content = Utils.createElement('div', {id: 'batch-content', style: {'margin-top': '1.5rem'}});

        this.renderTabContent(content, 'batches');

        container.appendChild(header);
        container.appendChild(tabs);
        container.appendChild(content);
    },

    async loadBatches() {
        try {
            const data = await API.batches.list();
            this.batches = data.batches || this.getMockBatches();
        } catch {
            this.batches = this.getMockBatches();
        }
    },

    getMockBatches() {
        return [
            {id: '1', name: 'KITTI Benchmark Suite', plugins: 4, datasets: 3, total: 12, completed: 12, failed: 0, running: 0, pending: 0, created: new Date(Date.now() - 86400000 * 2), status: 'completed'},
            {id: '2', name: 'Visual SLAM Comparison', plugins: 3, datasets: 2, total: 6, completed: 4, failed: 0, running: 2, pending: 0, created: new Date(Date.now() - 3600000), status: 'running'},
            {id: '3', name: 'EuRoC Evaluation', plugins: 2, datasets: 5, total: 10, completed: 0, failed: 0, running: 0, pending: 10, created: new Date(Date.now() - 1800000), status: 'pending'}
        ];
    },

    createTabs() {
        const tabs = [
            {id: 'batches', label: 'Batch Jobs', icon: '<path d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"></path>'},
            {id: 'matrix', label: 'Evaluation Matrix', icon: '<path d="M9 17V7m0 10a2 2 0 01-2 2H5a2 2 0 01-2-2V7a2 2 0 012-2h2a2 2 0 012 2m0 10a2 2 0 002 2h2a2 2 0 002-2M9 7a2 2 0 012-2h2a2 2 0 012 2m0 10V7m0 10a2 2 0 002 2h2a2 2 0 002-2V7a2 2 0 00-2-2h-2a2 2 0 00-2 2"></path>'}
        ];

        return Components.tabs(tabs, 0, (tab) => {
            this.renderTabContent(document.getElementById('batch-content'), tab.id);
        });
    },

    renderTabContent(container, tabId) {
        container.innerHTML = '';

        if (tabId === 'batches') {
            container.appendChild(this.renderBatchList());
        } else {
            container.appendChild(this.renderEvaluationMatrix());
        }
    },

    renderBatchList() {
        if (this.batches.length === 0) {
            return Components.emptyState({
                icon: '<path d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"></path>',
                title: 'No Batch Jobs',
                description: 'Create your first batch evaluation to run multiple tests',
                action: {
                    label: 'Create Batch',
                    onClick: () => this.createNewBatch()
                }
            });
        }

        return Utils.createElement('div', {
            class: 'stagger-fadeIn',
            style: {
                display: 'grid',
                'grid-template-columns': 'repeat(auto-fill, minmax(400px, 1fr))',
                gap: '1.5rem'
            }
        }, this.batches.map((batch, index) => this.createBatchCard(batch, index)));
    },

    createBatchCard(batch, index) {
        const card = Utils.createElement('div', {
            class: 'batch-card card hover-lift',
            style: {
                padding: '1.5rem',
                cursor: 'pointer',
                'animation-delay': `${index * 50}ms`
            },
            onclick: () => this.showBatchDetails(batch)
        });

        const header = Utils.createElement('div', {style: {display: 'flex', 'justify-content': 'space-between', 'align-items': 'flex-start', 'margin-bottom': '1rem'}}, [
            Utils.createElement('div', {style: {flex: '1', 'min-width': '0'}}, [
                Utils.createElement('h3', {style: {'font-size': '1.125rem', 'font-weight': '600', 'margin-bottom': '0.25rem', 'white-space': 'nowrap', overflow: 'hidden', 'text-overflow': 'ellipsis'}}, [document.createTextNode(batch.name)]),
                Utils.createElement('div', {style: {'font-size': '0.75rem', color: 'var(--text-tertiary)'}}, [
                    document.createTextNode(`${batch.plugins} plugins • ${batch.datasets} datasets • ${batch.total} evaluations`)
                ])
            ]),
            Components.badge(batch.status, batch.status === 'completed' ? 'success' : batch.status === 'running' ? 'warning' : 'info')
        ]);

        const progress = Utils.createElement('div', {style: {'margin-bottom': '1rem'}}, [
            Utils.createElement('div', {style: {display: 'flex', 'justify-content': 'space-between', 'margin-bottom': '0.5rem'}}, [
                Utils.createElement('span', {style: {'font-size': '0.75rem', color: 'var(--text-secondary)'}}, [document.createTextNode('Progress')]),
                Utils.createElement('span', {style: {'font-size': '0.75rem', 'font-weight': '600', color: 'var(--text-primary)'}}, [
                    document.createTextNode(`${batch.completed}/${batch.total}`)
                ])
            ]),
            Components.progress(batch.completed, batch.total)
        ]);

        const stats = Utils.createElement('div', {style: {display: 'grid', 'grid-template-columns': 'repeat(4, 1fr)', gap: '0.5rem', 'margin-bottom': '1rem'}}, [
            this.createMiniStat('Completed', batch.completed, 'success'),
            this.createMiniStat('Running', batch.running, 'warning'),
            this.createMiniStat('Pending', batch.pending, 'info'),
            this.createMiniStat('Failed', batch.failed, 'error')
        ]);

        const footer = Utils.createElement('div', {style: {display: 'flex', 'justify-content': 'space-between', 'align-items': 'center', 'padding-top': '1rem', 'border-top': '1px solid var(--border)'}}, [
            Utils.createElement('div', {style: {'font-size': '0.75rem', color: 'var(--text-tertiary)'}}, [document.createTextNode(Utils.formatRelativeTime(batch.created))]),
            Utils.createElement('div', {style: {display: 'flex', gap: '0.5rem'}},
                batch.status === 'running' ? [
                    Components.button('Pause', {size: 'sm', variant: 'secondary', onClick: (e) => {e.stopPropagation(); this.pauseBatch(batch);}}),
                    Components.button('Stop', {size: 'sm', variant: 'danger', onClick: (e) => {e.stopPropagation(); this.stopBatch(batch);}})
                ] : batch.status === 'pending' ? [
                    Components.button('Start', {size: 'sm', variant: 'primary', onClick: (e) => {e.stopPropagation(); this.startBatch(batch);}})
                ] : [
                    Components.button('View Results', {size: 'sm', variant: 'primary', onClick: (e) => {e.stopPropagation(); this.viewBatchResults(batch);}})
                ]
            )
        ]);

        card.appendChild(header);
        card.appendChild(progress);
        card.appendChild(stats);
        card.appendChild(footer);

        return card;
    },

    createMiniStat(label, value, variant) {
        return Utils.createElement('div', {style: {padding: '0.5rem', background: 'var(--bg-tertiary)', 'border-radius': 'var(--radius-md)', 'text-align': 'center'}}, [
            Utils.createElement('div', {style: {'font-size': '1rem', 'font-weight': '600', color: `var(--${variant})`}}, [document.createTextNode(value)]),
            Utils.createElement('div', {style: {'font-size': '0.625rem', color: 'var(--text-tertiary)', 'text-transform': 'uppercase', 'letter-spacing': '0.05em'}}, [document.createTextNode(label)])
        ]);
    },

    renderEvaluationMatrix() {
        const wrapper = Utils.createElement('div', {class: 'card', style: {padding: '1.5rem'}});

        const description = Utils.createElement('p', {style: {'font-size': '0.875rem', color: 'var(--text-secondary)', 'margin-bottom': '1.5rem'}}, [
            document.createTextNode('Configure a batch evaluation matrix by selecting plugins and datasets')
        ]);

        const pluginSelector = Utils.createElement('div', {style: {'margin-bottom': '1.5rem'}}, [
            Utils.createElement('h4', {style: {'font-size': '0.875rem', 'font-weight': '600', 'margin-bottom': '0.75rem'}}, [document.createTextNode('Select Plugins')]),
            Utils.createElement('div', {style: {display: 'flex', gap: '0.5rem', 'flex-wrap': 'wrap'}}, [
                this.createCheckableTag('ORB-SLAM3', true),
                this.createCheckableTag('VINS-Mono', true),
                this.createCheckableTag('DSO', false),
                this.createCheckableTag('LIO-SAM', true),
                this.createCheckableTag('Cartographer', false)
            ])
        ]);

        const datasetSelector = Utils.createElement('div', {style: {'margin-bottom': '1.5rem'}}, [
            Utils.createElement('h4', {style: {'font-size': '0.875rem', 'font-weight': '600', 'margin-bottom': '0.75rem'}}, [document.createTextNode('Select Datasets')]),
            Utils.createElement('div', {style: {display: 'flex', gap: '0.5rem', 'flex-wrap': 'wrap'}}, [
                this.createCheckableTag('KITTI-00', true),
                this.createCheckableTag('KITTI-05', true),
                this.createCheckableTag('EuRoC MH-01', true),
                this.createCheckableTag('TUM RGB-D', false)
            ])
        ]);

        const matrixPreview = this.createMatrixPreview();

        const actions = Utils.createElement('div', {style: {display: 'flex', gap: '1rem', 'padding-top': '1.5rem', 'border-top': '1px solid var(--border)'}}, [
            Components.button('Clear All', {variant: 'secondary', onClick: () => this.clearMatrix()}),
            Components.button('Run Batch Evaluation', {variant: 'primary', onClick: () => this.runMatrixEvaluation()})
        ]);

        wrapper.appendChild(description);
        wrapper.appendChild(pluginSelector);
        wrapper.appendChild(datasetSelector);
        wrapper.appendChild(matrixPreview);
        wrapper.appendChild(actions);

        return wrapper;
    },

    createCheckableTag(label, checked) {
        const tag = Utils.createElement('button', {
            style: {
                padding: '0.5rem 1rem',
                border: `2px solid ${checked ? 'var(--primary)' : 'var(--border)'}`,
                background: checked ? 'rgba(37, 99, 235, 0.1)' : 'var(--bg-primary)',
                color: checked ? 'var(--primary)' : 'var(--text-secondary)',
                'border-radius': 'var(--radius-lg)',
                cursor: 'pointer',
                'font-size': '0.875rem',
                'font-weight': '500',
                display: 'flex',
                'align-items': 'center',
                gap: '0.5rem',
                transition: 'all var(--duration-fast) var(--ease)'
            },
            onclick: function() {
                const isChecked = this.style.borderColor.includes('37');
                this.style.borderColor = isChecked ? 'var(--border)' : 'var(--primary)';
                this.style.background = isChecked ? 'var(--bg-primary)' : 'rgba(37, 99, 235, 0.1)';
                this.style.color = isChecked ? 'var(--text-secondary)' : 'var(--primary)';
                const icon = this.querySelector('svg');
                if (icon) icon.style.display = isChecked ? 'none' : 'block';
            }
        }, [
            checked ? Utils.createElement('svg', {style: {width: '1rem', height: '1rem'}, viewBox: '0 0 24 24', fill: 'none', stroke: 'currentColor', 'stroke-width': '2'}, []).innerHTML = '<path d="M5 13l4 4L19 7"></path>' : null,
            document.createTextNode(label)
        ].filter(Boolean));

        return tag;
    },

    createMatrixPreview() {
        return Utils.createElement('div', {style: {'margin-bottom': '1.5rem'}}, [
            Utils.createElement('h4', {style: {'font-size': '0.875rem', 'font-weight': '600', 'margin-bottom': '0.75rem'}}, [document.createTextNode('Matrix Preview')]),
            Utils.createElement('div', {class: 'card', style: {padding: '1.5rem', background: 'var(--bg-tertiary)'}}, [
                Utils.createElement('div', {style: {display: 'flex', 'align-items': 'center', 'justify-content': 'center', gap: '1rem'}}, [
                    Utils.createElement('div', {style: {'text-align': 'center'}}, [
                        Utils.createElement('div', {style: {'font-size': '2rem', 'font-weight': '700', color: 'var(--primary)', 'margin-bottom': '0.25rem'}}, [document.createTextNode('3')]),
                        Utils.createElement('div', {style: {'font-size': '0.75rem', color: 'var(--text-secondary)'}}, [document.createTextNode('Plugins')])
                    ]),
                    Utils.createElement('svg', {style: {width: '1.5rem', height: '1.5rem', color: 'var(--text-tertiary)'}, viewBox: '0 0 24 24', fill: 'none', stroke: 'currentColor', 'stroke-width': '2'}, []).innerHTML = '<path d="M6 18L18 6M6 6l12 12"></path>',
                    Utils.createElement('div', {style: {'text-align': 'center'}}, [
                        Utils.createElement('div', {style: {'font-size': '2rem', 'font-weight': '700', color: 'var(--success)', 'margin-bottom': '0.25rem'}}, [document.createTextNode('3')]),
                        Utils.createElement('div', {style: {'font-size': '0.75rem', color: 'var(--text-secondary)'}}, [document.createTextNode('Datasets')])
                    ]),
                    Utils.createElement('svg', {style: {width: '1.5rem', height: '1.5rem', color: 'var(--text-tertiary)'}, viewBox: '0 0 24 24', fill: 'none', stroke: 'currentColor', 'stroke-width': '2'}, []).innerHTML = '<path d="M13 7l5 5m0 0l-5 5m5-5H6"></path>',
                    Utils.createElement('div', {style: {'text-align': 'center'}}, [
                        Utils.createElement('div', {style: {'font-size': '2rem', 'font-weight': '700', color: 'var(--warning)', 'margin-bottom': '0.25rem'}}, [document.createTextNode('9')]),
                        Utils.createElement('div', {style: {'font-size': '0.75rem', color: 'var(--text-secondary)'}}, [document.createTextNode('Evaluations')])
                    ])
                ])
            ])
        ]);
    },

    showBatchDetails(batch) {
        const content = Utils.createElement('div', {}, [
            Utils.createElement('div', {style: {display: 'grid', 'grid-template-columns': 'repeat(2, 1fr)', gap: '1.5rem', 'margin-bottom': '2rem'}}, [
                Utils.createElement('div', {}, [
                    Utils.createElement('h4', {style: {'font-size': '0.875rem', 'font-weight': '600', 'margin-bottom': '1rem', color: 'var(--text-secondary)', 'text-transform': 'uppercase', 'letter-spacing': '0.05em'}}, [document.createTextNode('Batch Details')]),
                    Utils.createElement('div', {style: {display: 'grid', gap: '0.75rem'}}, [
                        this.createDetailRow('Status', Components.badge(batch.status, batch.status === 'completed' ? 'success' : batch.status === 'running' ? 'warning' : 'info')),
                        this.createDetailRow('Created', Utils.formatDateTime(batch.created)),
                        this.createDetailRow('Plugins', batch.plugins),
                        this.createDetailRow('Datasets', batch.datasets),
                        this.createDetailRow('Total Evaluations', batch.total)
                    ])
                ]),
                Utils.createElement('div', {}, [
                    Utils.createElement('h4', {style: {'font-size': '0.875rem', 'font-weight': '600', 'margin-bottom': '1rem', color: 'var(--text-secondary)', 'text-transform': 'uppercase', 'letter-spacing': '0.05em'}}, [document.createTextNode('Progress')]),
                    Utils.createElement('div', {style: {display: 'grid', gap: '0.75rem'}}, [
                        this.createDetailRow('Completed', `${batch.completed} (${((batch.completed / batch.total) * 100).toFixed(1)}%)`),
                        this.createDetailRow('Running', batch.running),
                        this.createDetailRow('Pending', batch.pending),
                        this.createDetailRow('Failed', batch.failed)
                    ])
                ])
            ]),
            Utils.createElement('div', {}, [
                Utils.createElement('h4', {style: {'font-size': '0.875rem', 'font-weight': '600', 'margin-bottom': '1rem', color: 'var(--text-secondary)', 'text-transform': 'uppercase', 'letter-spacing': '0.05em'}}, [document.createTextNode('Progress Visualization')]),
                Utils.createElement('div', {style: {'margin-bottom': '0.5rem'}}, [Components.progress(batch.completed, batch.total)])
            ])
        ]);

        Components.modal(batch.name, content, {
            size: 'large',
            actions: batch.status === 'completed' ? [
                {label: 'View Results', variant: 'primary', onClick: () => this.viewBatchResults(batch)}
            ] : []
        });
    },

    createDetailRow(label, value) {
        return Utils.createElement('div', {style: {display: 'flex', 'justify-content': 'space-between', 'align-items': 'center'}}, [
            Utils.createElement('span', {style: {'font-size': '0.875rem', color: 'var(--text-secondary)'}}, [document.createTextNode(label)]),
            typeof value === 'string' || typeof value === 'number'
                ? Utils.createElement('span', {style: {'font-size': '0.875rem', 'font-weight': '600', color: 'var(--text-primary)'}}, [document.createTextNode(value)])
                : value
        ]);
    },

    createNewBatch() {
        Components.toast('Opening batch evaluation creator', 'info');
        this.renderTabContent(document.getElementById('batch-content'), 'matrix');
    },

    startBatch(batch) {
        Components.toast(`Starting batch: ${batch.name}`, 'success');
    },

    pauseBatch(batch) {
        Components.toast(`Pausing batch: ${batch.name}`, 'warning');
    },

    stopBatch(batch) {
        Components.confirm(`Are you sure you want to stop "${batch.name}"?`, {
            confirmText: 'Stop Batch',
            onConfirm: () => {
                Components.toast(`Batch stopped: ${batch.name}`, 'warning');
            }
        });
    },

    viewBatchResults(batch) {
        App.navigate('results');
    },

    clearMatrix() {
        Components.toast('Matrix cleared', 'info');
    },

    runMatrixEvaluation() {
        Components.toast('Starting batch evaluation...', 'success');
        setTimeout(() => {
            this.renderTabContent(document.getElementById('batch-content'), 'batches');
        }, 1500);
    }
};
