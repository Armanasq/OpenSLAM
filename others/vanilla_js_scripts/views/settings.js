const SettingsView = {
    settings: {},

    async render() {
        const container = document.getElementById('view-settings');
        container.innerHTML = '';

        await this.loadSettings();

        const header = Utils.createElement('div', {style: {'margin-bottom': '2rem'}}, [
            Utils.createElement('h2', {style: {'font-size': '1.5rem', 'font-weight': '700', color: 'var(--text-primary)', 'margin-bottom': '0.25rem'}}, [document.createTextNode('Settings')]),
            Utils.createElement('p', {style: {'font-size': '0.875rem', color: 'var(--text-secondary)'}}, [document.createTextNode('Configure your OpenSLAM environment')])
        ]);

        const sections = Utils.createElement('div', {style: {display: 'grid', gap: '1.5rem'}}, [
            this.createGeneralSettings(),
            this.createEvaluationSettings(),
            this.createStorageSettings(),
            this.createAdvancedSettings()
        ]);

        const actions = Utils.createElement('div', {style: {display: 'flex', gap: '1rem', 'justify-content': 'flex-end', 'margin-top': '2rem', 'padding-top': '1.5rem', 'border-top': '1px solid var(--border)'}}, [
            Components.button('Reset to Defaults', {variant: 'secondary', onClick: () => this.resetSettings()}),
            Components.button('Save Changes', {variant: 'primary', onClick: () => this.saveSettings()})
        ]);

        container.appendChild(header);
        container.appendChild(sections);
        container.appendChild(actions);
    },

    async loadSettings() {
        try {
            const data = await API.system.settings();
            this.settings = data.settings || this.getDefaultSettings();
        } catch {
            this.settings = this.getDefaultSettings();
        }
    },

    getDefaultSettings() {
        return {
            theme: 'light',
            language: 'en',
            autoSave: true,
            notifications: true,
            defaultMetric: 'ate',
            maxConcurrentEvaluations: 3,
            cacheResults: true,
            logLevel: 'info',
            dataPath: '/data/openslam',
            maxStorageSize: 100,
            autoCleanup: true,
            retentionDays: 30
        };
    },

    createGeneralSettings() {
        return Utils.createElement('div', {class: 'card animate-slideUp', style: {padding: '1.5rem'}}, [
            Utils.createElement('h3', {style: {'font-size': '1.125rem', 'font-weight': '600', 'margin-bottom': '1.5rem', 'padding-bottom': '1rem', 'border-bottom': '1px solid var(--border)'}}, [document.createTextNode('General')]),
            Utils.createElement('div', {style: {display: 'grid', gap: '1.5rem'}}, [
                Components.select({
                    label: 'Theme',
                    options: [
                        {value: 'light', label: 'Light'},
                        {value: 'dark', label: 'Dark'},
                        {value: 'auto', label: 'Auto (System)'}
                    ],
                    value: this.settings.theme,
                    onChange: (value) => this.settings.theme = value
                }),
                Components.select({
                    label: 'Language',
                    options: [
                        {value: 'en', label: 'English'},
                        {value: 'zh', label: '中文'},
                        {value: 'ja', label: '日本語'},
                        {value: 'es', label: 'Español'}
                    ],
                    value: this.settings.language,
                    onChange: (value) => this.settings.language = value
                }),
                Utils.createElement('div', {style: {display: 'grid', gap: '1rem'}}, [
                    Components.switch({
                        label: 'Auto-save results',
                        checked: this.settings.autoSave,
                        onChange: (checked) => this.settings.autoSave = checked
                    }),
                    Components.switch({
                        label: 'Enable notifications',
                        checked: this.settings.notifications,
                        onChange: (checked) => this.settings.notifications = checked
                    })
                ])
            ])
        ]);
    },

    createEvaluationSettings() {
        return Utils.createElement('div', {class: 'card animate-slideUp', style: {padding: '1.5rem', 'animation-delay': '50ms'}}, [
            Utils.createElement('h3', {style: {'font-size': '1.125rem', 'font-weight': '600', 'margin-bottom': '1.5rem', 'padding-bottom': '1rem', 'border-bottom': '1px solid var(--border)'}}, [document.createTextNode('Evaluation')]),
            Utils.createElement('div', {style: {display: 'grid', gap: '1.5rem'}}, [
                Components.select({
                    label: 'Default Metric',
                    options: [
                        {value: 'ate', label: 'Absolute Trajectory Error (ATE)'},
                        {value: 'rpe', label: 'Relative Pose Error (RPE)'},
                        {value: 'both', label: 'Both ATE and RPE'}
                    ],
                    value: this.settings.defaultMetric,
                    onChange: (value) => this.settings.defaultMetric = value
                }),
                Components.input({
                    label: 'Max Concurrent Evaluations',
                    type: 'number',
                    value: this.settings.maxConcurrentEvaluations,
                    min: '1',
                    max: '10',
                    onInput: (e) => this.settings.maxConcurrentEvaluations = parseInt(e.target.value)
                }),
                Utils.createElement('div', {}, [
                    Components.switch({
                        label: 'Cache evaluation results',
                        checked: this.settings.cacheResults,
                        onChange: (checked) => this.settings.cacheResults = checked
                    }),
                    Utils.createElement('p', {style: {'font-size': '0.75rem', color: 'var(--text-tertiary)', 'margin-top': '0.5rem', 'margin-left': '2.5rem'}}, [
                        document.createTextNode('Store intermediate results to resume failed evaluations')
                    ])
                ])
            ])
        ]);
    },

    createStorageSettings() {
        return Utils.createElement('div', {class: 'card animate-slideUp', style: {padding: '1.5rem', 'animation-delay': '100ms'}}, [
            Utils.createElement('h3', {style: {'font-size': '1.125rem', 'font-weight': '600', 'margin-bottom': '1.5rem', 'padding-bottom': '1rem', 'border-bottom': '1px solid var(--border)'}}, [document.createTextNode('Storage')]),
            Utils.createElement('div', {style: {display: 'grid', gap: '1.5rem'}}, [
                Components.input({
                    label: 'Data Directory Path',
                    value: this.settings.dataPath,
                    placeholder: '/path/to/data',
                    onInput: (e) => this.settings.dataPath = e.target.value
                }),
                Utils.createElement('div', {}, [
                    Utils.createElement('label', {style: {'font-size': '0.875rem', 'font-weight': '500', color: 'var(--text-primary)', 'margin-bottom': '0.5rem', display: 'block'}}, [document.createTextNode('Max Storage Size (GB)')]),
                    Utils.createElement('div', {style: {display: 'flex', 'align-items': 'center', gap: '1rem'}}, [
                        Utils.createElement('input', {
                            type: 'range',
                            min: '10',
                            max: '1000',
                            value: this.settings.maxStorageSize,
                            style: {flex: '1'},
                            oninput: (e) => {
                                this.settings.maxStorageSize = parseInt(e.target.value);
                                e.target.nextElementSibling.textContent = e.target.value + ' GB';
                            }
                        }),
                        Utils.createElement('span', {style: {'font-size': '0.875rem', 'font-weight': '600', color: 'var(--text-primary)', 'min-width': '80px', 'text-align': 'right'}}, [
                            document.createTextNode(this.settings.maxStorageSize + ' GB')
                        ])
                    ])
                ]),
                Utils.createElement('div', {}, [
                    Components.switch({
                        label: 'Auto-cleanup old results',
                        checked: this.settings.autoCleanup,
                        onChange: (checked) => this.settings.autoCleanup = checked
                    }),
                    Utils.createElement('p', {style: {'font-size': '0.75rem', color: 'var(--text-tertiary)', 'margin-top': '0.5rem', 'margin-left': '2.5rem'}}, [
                        document.createTextNode('Automatically delete results older than retention period')
                    ])
                ]),
                Components.input({
                    label: 'Retention Period (days)',
                    type: 'number',
                    value: this.settings.retentionDays,
                    min: '1',
                    max: '365',
                    disabled: !this.settings.autoCleanup,
                    onInput: (e) => this.settings.retentionDays = parseInt(e.target.value)
                }),
                Utils.createElement('div', {class: 'card', style: {padding: '1rem', background: 'var(--bg-tertiary)'}}, [
                    Utils.createElement('div', {style: {display: 'flex', 'justify-content': 'space-between', 'align-items': 'center', 'margin-bottom': '0.75rem'}}, [
                        Utils.createElement('span', {style: {'font-size': '0.875rem', color: 'var(--text-secondary)'}}, [document.createTextNode('Current Storage Usage')]),
                        Utils.createElement('span', {style: {'font-size': '0.875rem', 'font-weight': '600'}}, [document.createTextNode('12.5 GB / 100 GB')])
                    ]),
                    Components.progress(12.5, 100),
                    Utils.createElement('div', {style: {display: 'flex', 'justify-content': 'space-between', 'margin-top': '0.75rem'}}, [
                        Utils.createElement('span', {style: {'font-size': '0.75rem', color: 'var(--text-tertiary)'}}, [document.createTextNode('Datasets: 8.2 GB')]),
                        Utils.createElement('span', {style: {'font-size': '0.75rem', color: 'var(--text-tertiary)'}}, [document.createTextNode('Results: 4.3 GB')])
                    ])
                ])
            ])
        ]);
    },

    createAdvancedSettings() {
        return Utils.createElement('div', {class: 'card animate-slideUp', style: {padding: '1.5rem', 'animation-delay': '150ms'}}, [
            Utils.createElement('h3', {style: {'font-size': '1.125rem', 'font-weight': '600', 'margin-bottom': '1.5rem', 'padding-bottom': '1rem', 'border-bottom': '1px solid var(--border)'}}, [document.createTextNode('Advanced')]),
            Utils.createElement('div', {style: {display: 'grid', gap: '1.5rem'}}, [
                Components.select({
                    label: 'Log Level',
                    options: [
                        {value: 'debug', label: 'Debug'},
                        {value: 'info', label: 'Info'},
                        {value: 'warning', label: 'Warning'},
                        {value: 'error', label: 'Error'}
                    ],
                    value: this.settings.logLevel,
                    onChange: (value) => this.settings.logLevel = value
                }),
                Utils.createElement('div', {class: 'card', style: {padding: '1.5rem', background: 'var(--bg-tertiary)', border: '1px solid var(--border-dark)'}}, [
                    Utils.createElement('div', {style: {display: 'flex', 'align-items': 'flex-start', gap: '1rem'}}, [
                        Utils.createElement('svg', {style: {width: '1.5rem', height: '1.5rem', color: 'var(--warning)', 'flex-shrink': '0', 'margin-top': '0.125rem'}, viewBox: '0 0 24 24', fill: 'none', stroke: 'currentColor', 'stroke-width': '2'}, []).innerHTML = '<path d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"></path>',
                        Utils.createElement('div', {style: {flex: '1'}}, [
                            Utils.createElement('h4', {style: {'font-size': '0.875rem', 'font-weight': '600', 'margin-bottom': '0.5rem'}}, [document.createTextNode('Danger Zone')]),
                            Utils.createElement('p', {style: {'font-size': '0.75rem', color: 'var(--text-secondary)', 'margin-bottom': '1rem'}}, [
                                document.createTextNode('These actions cannot be undone. Please be careful.')
                            ]),
                            Utils.createElement('div', {style: {display: 'flex', 'flex-direction': 'column', gap: '0.75rem'}}, [
                                Components.button('Clear All Cache', {
                                    variant: 'secondary',
                                    size: 'sm',
                                    onClick: () => this.clearCache()
                                }),
                                Components.button('Delete All Results', {
                                    variant: 'danger',
                                    size: 'sm',
                                    onClick: () => this.deleteAllResults()
                                }),
                                Components.button('Reset Application', {
                                    variant: 'danger',
                                    size: 'sm',
                                    onClick: () => this.resetApplication()
                                })
                            ])
                        ])
                    ])
                ])
            ])
        ]);
    },

    saveSettings() {
        Components.toast('Saving settings...', 'info');
        setTimeout(() => {
            Components.toast('Settings saved successfully', 'success');
        }, 500);
    },

    resetSettings() {
        Components.confirm('Are you sure you want to reset all settings to defaults?', {
            confirmText: 'Reset Settings',
            onConfirm: () => {
                this.settings = this.getDefaultSettings();
                this.render();
                Components.toast('Settings reset to defaults', 'success');
            }
        });
    },

    clearCache() {
        Components.confirm('Clear all cached data? This will not delete your datasets or results.', {
            confirmText: 'Clear Cache',
            onConfirm: () => {
                Components.toast('Cache cleared successfully', 'success');
            }
        });
    },

    deleteAllResults() {
        Components.confirm('Delete all evaluation results? This action cannot be undone.', {
            confirmText: 'Delete All Results',
            variant: 'danger',
            onConfirm: () => {
                Components.toast('All results deleted', 'warning');
            }
        });
    },

    resetApplication() {
        Components.confirm('Reset the entire application? This will delete all data including datasets, results, and settings.', {
            confirmText: 'Reset Application',
            variant: 'danger',
            onConfirm: () => {
                Components.toast('Application reset', 'warning');
                setTimeout(() => {
                    window.location.reload();
                }, 2000);
            }
        });
    }
};
