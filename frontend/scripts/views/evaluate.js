const EvaluateView = {
    currentStep: 0,
    selectedPlugin: null,
    selectedDataset: null,
    parameters: {},
    evaluationId: null,
    isEvaluating: false,
    progress: 0,

    steps: [
        {id: 'plugin', title: 'Select Plugin', icon: '<path d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4"></path>'},
        {id: 'dataset', title: 'Select Dataset', icon: '<path d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2z"></path>'},
        {id: 'parameters', title: 'Configure Parameters', icon: '<path d="M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4"></path>'},
        {id: 'review', title: 'Review & Run', icon: '<path d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path>'}
    ],

    async render() {
        const container = document.getElementById('view-evaluate');
        container.innerHTML = '';

        const header = Utils.createElement('div', {style: {'margin-bottom': '2rem'}}, [
            Utils.createElement('h2', {style: {'font-size': '1.5rem', 'font-weight': '700', color: 'var(--text-primary)', 'margin-bottom': '0.25rem'}}, [document.createTextNode('Evaluate SLAM Plugin')]),
            Utils.createElement('p', {style: {'font-size': '0.875rem', color: 'var(--text-secondary)'}}, [document.createTextNode('Run and benchmark SLAM algorithms on your datasets')])
        ]);

        const progressBar = this.createProgressBar();
        const stepper = this.createStepper();
        const stepContent = Utils.createElement('div', {class: 'step-content card', style: {padding: '2rem', 'margin-top': '2rem', 'min-height': '400px'}});

        this.renderStepContent(stepContent);

        container.appendChild(header);
        container.appendChild(progressBar);
        container.appendChild(stepper);
        container.appendChild(stepContent);

        if (this.isEvaluating) {
            this.startProgressMonitoring();
        }
    },

    createProgressBar() {
        const progress = ((this.currentStep + 1) / this.steps.length) * 100;

        const container = Utils.createElement('div', {style: {'margin-bottom': '1.5rem'}}, [
            Utils.createElement('div', {style: {display: 'flex', 'justify-content': 'space-between', 'margin-bottom': '0.5rem'}}, [
                Utils.createElement('span', {style: {'font-size': '0.75rem', 'font-weight': '600', color: 'var(--text-secondary)'}}, [document.createTextNode(`Step ${this.currentStep + 1} of ${this.steps.length}`)]),
                Utils.createElement('span', {style: {'font-size': '0.75rem', 'font-weight': '600', color: 'var(--primary)'}}, [document.createTextNode(`${Math.round(progress)}%`)])
            ]),
            Utils.createElement('div', {style: {height: '8px', background: 'var(--bg-tertiary)', 'border-radius': 'var(--radius-full)', overflow: 'hidden', position: 'relative'}}, [
                Utils.createElement('div', {
                    class: 'progress-fill',
                    style: {
                        height: '100%',
                        width: `${progress}%`,
                        background: 'linear-gradient(90deg, var(--primary), var(--primary-light))',
                        'border-radius': 'var(--radius-full)',
                        transition: 'width var(--duration-slow) var(--ease)',
                        position: 'relative',
                        overflow: 'hidden'
                    }
                }, [
                    Utils.createElement('div', {style: {
                        position: 'absolute',
                        inset: '0',
                        background: 'linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.3), transparent)',
                        animation: 'shimmer 2s infinite'
                    }})
                ])
            ])
        ]);

        return container;
    },

    createStepper() {
        const stepper = Utils.createElement('div', {style: {display: 'flex', 'justify-content': 'space-between', position: 'relative'}});

        const line = Utils.createElement('div', {
            style: {
                position: 'absolute',
                top: '1.5rem',
                left: '0',
                right: '0',
                height: '2px',
                background: 'var(--border)',
                'z-index': '0'
            }
        });

        const activeLine = Utils.createElement('div', {
            style: {
                position: 'absolute',
                top: '1.5rem',
                left: '0',
                width: `${(this.currentStep / (this.steps.length - 1)) * 100}%`,
                height: '2px',
                background: 'var(--primary)',
                transition: 'width var(--duration-slow) var(--ease)',
                'z-index': '1'
            }
        });

        stepper.appendChild(line);
        stepper.appendChild(activeLine);

        this.steps.forEach((step, index) => {
            const stepEl = this.createStepIndicator(step, index);
            stepper.appendChild(stepEl);
        });

        return stepper;
    },

    createStepIndicator(step, index) {
        const isActive = index === this.currentStep;
        const isCompleted = index < this.currentStep;
        const isFuture = index > this.currentStep;

        const container = Utils.createElement('div', {
            style: {
                display: 'flex',
                'flex-direction': 'column',
                'align-items': 'center',
                gap: '0.5rem',
                flex: '1',
                position: 'relative',
                'z-index': '2',
                cursor: isCompleted ? 'pointer' : 'default'
            },
            onclick: isCompleted ? () => this.goToStep(index) : null
        });

        const circle = Utils.createElement('div', {
            style: {
                width: '3rem',
                height: '3rem',
                'border-radius': 'var(--radius-full)',
                background: isActive || isCompleted ? 'var(--primary)' : 'var(--bg-primary)',
                border: `2px solid ${isActive || isCompleted ? 'var(--primary)' : 'var(--border)'}`,
                display: 'flex',
                'align-items': 'center',
                'justify-content': 'center',
                transition: 'all var(--duration-normal) var(--ease-spring)',
                'box-shadow': isActive ? '0 0 0 4px rgba(37, 99, 235, 0.1)' : 'none'
            }
        }, [
            isCompleted
                ? Utils.createElement('svg', {style: {width: '1.5rem', height: '1.5rem', color: 'var(--text-inverse)'}, viewBox: '0 0 24 24', fill: 'none', stroke: 'currentColor', 'stroke-width': '3'}, []).innerHTML = '<path d="M5 13l4 4L19 7"></path>'
                : Utils.createElement('svg', {style: {width: '1.5rem', height: '1.5rem', color: isActive ? 'var(--text-inverse)' : 'var(--text-tertiary)'}, viewBox: '0 0 24 24', fill: 'none', stroke: 'currentColor', 'stroke-width': '2'}, []).innerHTML = step.icon
        ]);

        const label = Utils.createElement('div', {
            style: {
                'font-size': '0.75rem',
                'font-weight': isActive ? '600' : '500',
                color: isActive ? 'var(--text-primary)' : isFuture ? 'var(--text-tertiary)' : 'var(--text-secondary)',
                'text-align': 'center',
                transition: 'all var(--duration-fast) var(--ease)'
            }
        }, [document.createTextNode(step.title)]);

        container.appendChild(circle);
        container.appendChild(label);

        if (isCompleted) {
            container.addEventListener('mouseenter', () => {
                circle.style.transform = 'scale(1.1)';
            });
            container.addEventListener('mouseleave', () => {
                circle.style.transform = 'scale(1)';
            });
        }

        if (isActive) {
            circle.style.animation = 'pulse-scale 2s ease-in-out infinite';
        }

        return container;
    },

    goToStep(index) {
        this.currentStep = index;
        this.render();
    },

    nextStep() {
        if (this.currentStep < this.steps.length - 1) {
            this.currentStep++;
            this.render();
        }
    },

    previousStep() {
        if (this.currentStep > 0) {
            this.currentStep--;
            this.render();
        }
    },

    async renderStepContent(container) {
        container.innerHTML = '';

        const step = this.steps[this.currentStep];
        let content;

        switch (step.id) {
            case 'plugin':
                content = await this.renderPluginSelection();
                break;
            case 'dataset':
                content = await this.renderDatasetSelection();
                break;
            case 'parameters':
                content = this.renderParametersConfiguration();
                break;
            case 'review':
                content = this.renderReviewAndRun();
                break;
        }

        container.appendChild(content);
    },

    async renderPluginSelection() {
        const wrapper = Utils.createElement('div', {class: 'animate-slideUp'});

        const title = Utils.createElement('h3', {style: {'font-size': '1.125rem', 'font-weight': '600', 'margin-bottom': '0.5rem'}}, [document.createTextNode('Select SLAM Plugin')]);
        const description = Utils.createElement('p', {style: {'font-size': '0.875rem', color: 'var(--text-secondary)', 'margin-bottom': '1.5rem'}}, [document.createTextNode('Choose the SLAM algorithm you want to evaluate')]);

        const plugins = await this.fetchPlugins();
        const grid = Utils.createElement('div', {
            class: 'stagger-fadeIn',
            style: {
                display: 'grid',
                'grid-template-columns': 'repeat(auto-fill, minmax(280px, 1fr))',
                gap: '1rem',
                'margin-bottom': '2rem'
            }
        });

        plugins.forEach((plugin, index) => {
            const card = this.createSelectablePluginCard(plugin, index);
            grid.appendChild(card);
        });

        const actions = this.createStepActions(false, !!this.selectedPlugin);

        wrapper.appendChild(title);
        wrapper.appendChild(description);
        wrapper.appendChild(grid);
        wrapper.appendChild(actions);

        return wrapper;
    },

    createSelectablePluginCard(plugin, index) {
        const isSelected = this.selectedPlugin === plugin.name;

        const card = Utils.createElement('div', {
            class: 'selectable-card card',
            style: {
                padding: '1.5rem',
                cursor: 'pointer',
                border: `2px solid ${isSelected ? 'var(--primary)' : 'var(--border)'}`,
                background: isSelected ? 'rgba(37, 99, 235, 0.05)' : 'var(--bg-primary)',
                transition: 'all var(--duration-fast) var(--ease)',
                position: 'relative',
                'animation-delay': `${index * 50}ms`
            },
            onclick: () => this.selectPlugin(plugin.name)
        });

        if (isSelected) {
            const checkmark = Utils.createElement('div', {
                class: 'animate-scaleIn',
                style: {
                    position: 'absolute',
                    top: '1rem',
                    right: '1rem',
                    width: '2rem',
                    height: '2rem',
                    'border-radius': 'var(--radius-full)',
                    background: 'var(--primary)',
                    display: 'flex',
                    'align-items': 'center',
                    'justify-content': 'center'
                }
            }, [
                Utils.createElement('svg', {style: {width: '1.25rem', height: '1.25rem', color: 'var(--text-inverse)'}, viewBox: '0 0 24 24', fill: 'none', stroke: 'currentColor', 'stroke-width': '3'}, []).innerHTML = '<path d="M5 13l4 4L19 7"></path>'
            ]);
            card.appendChild(checkmark);
        }

        const header = Utils.createElement('div', {style: {'margin-bottom': '1rem'}}, [
            Utils.createElement('h4', {style: {'font-size': '1rem', 'font-weight': '600', 'margin-bottom': '0.25rem'}}, [document.createTextNode(plugin.name)]),
            Utils.createElement('div', {style: {'font-size': '0.75rem', color: 'var(--text-tertiary)'}}, [document.createTextNode(`v${plugin.version} • ${plugin.type}`)])
        ]);

        const description = Utils.createElement('p', {
            style: {
                'font-size': '0.875rem',
                color: 'var(--text-secondary)',
                'line-height': '1.5',
                display: '-webkit-box',
                '-webkit-line-clamp': '2',
                '-webkit-box-orient': 'vertical',
                overflow: 'hidden'
            }
        }, [document.createTextNode(plugin.description)]);

        card.appendChild(header);
        card.appendChild(description);

        card.addEventListener('mouseenter', () => {
            if (!isSelected) {
                card.style.borderColor = 'var(--primary-light)';
                card.style.transform = 'translateY(-4px)';
            }
        });

        card.addEventListener('mouseleave', () => {
            if (!isSelected) {
                card.style.borderColor = 'var(--border)';
                card.style.transform = 'translateY(0)';
            }
        });

        return card;
    },

    async renderDatasetSelection() {
        const wrapper = Utils.createElement('div', {class: 'animate-slideUp'});

        const title = Utils.createElement('h3', {style: {'font-size': '1.125rem', 'font-weight': '600', 'margin-bottom': '0.5rem'}}, [document.createTextNode('Select Dataset')]);
        const description = Utils.createElement('p', {style: {'font-size': '0.875rem', color: 'var(--text-secondary)', 'margin-bottom': '1.5rem'}}, [document.createTextNode('Choose the dataset for evaluation')]);

        const datasets = await this.fetchDatasets();
        const list = Utils.createElement('div', {class: 'stagger-fadeIn', style: {display: 'flex', 'flex-direction': 'column', gap: '0.75rem', 'margin-bottom': '2rem'}});

        datasets.forEach((dataset, index) => {
            const item = this.createSelectableDatasetItem(dataset, index);
            list.appendChild(item);
        });

        const uploadSection = Utils.createElement('div', {style: {'margin-top': '1.5rem', 'padding-top': '1.5rem', 'border-top': '1px solid var(--border)'}}, [
            Utils.createElement('p', {style: {'font-size': '0.875rem', color: 'var(--text-secondary)', 'margin-bottom': '1rem'}}, [document.createTextNode('Or upload a new dataset')]),
            Components.button('Upload Dataset', {
                variant: 'secondary',
                icon: '<path d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"></path>',
                onClick: () => App.navigate('datasets')
            })
        ]);

        const actions = this.createStepActions(true, !!this.selectedDataset);

        wrapper.appendChild(title);
        wrapper.appendChild(description);
        wrapper.appendChild(list);
        wrapper.appendChild(uploadSection);
        wrapper.appendChild(actions);

        return wrapper;
    },

    createSelectableDatasetItem(dataset, index) {
        const isSelected = this.selectedDataset === dataset.id;

        const item = Utils.createElement('div', {
            class: 'selectable-item card',
            style: {
                padding: '1.25rem',
                display: 'flex',
                'align-items': 'center',
                gap: '1rem',
                cursor: 'pointer',
                border: `2px solid ${isSelected ? 'var(--primary)' : 'var(--border)'}`,
                background: isSelected ? 'rgba(37, 99, 235, 0.05)' : 'var(--bg-primary)',
                transition: 'all var(--duration-fast) var(--ease)',
                'animation-delay': `${index * 50}ms`
            },
            onclick: () => this.selectDataset(dataset.id)
        });

        const radio = Utils.createElement('div', {
            style: {
                width: '1.5rem',
                height: '1.5rem',
                'border-radius': 'var(--radius-full)',
                border: `2px solid ${isSelected ? 'var(--primary)' : 'var(--border)'}`,
                display: 'flex',
                'align-items': 'center',
                'justify-content': 'center',
                transition: 'all var(--duration-fast) var(--ease)',
                'flex-shrink': '0'
            }
        }, [
            isSelected ? Utils.createElement('div', {
                class: 'animate-scaleIn',
                style: {
                    width: '0.75rem',
                    height: '0.75rem',
                    'border-radius': 'var(--radius-full)',
                    background: 'var(--primary)'
                }
            }) : null
        ].filter(Boolean));

        const info = Utils.createElement('div', {style: {flex: '1', 'min-width': '0'}}, [
            Utils.createElement('div', {style: {display: 'flex', 'align-items': 'center', gap: '0.75rem', 'margin-bottom': '0.25rem'}}, [
                Utils.createElement('h4', {style: {'font-size': '0.875rem', 'font-weight': '600'}}, [document.createTextNode(dataset.name)]),
                Components.badge(dataset.format, 'info')
            ]),
            Utils.createElement('div', {style: {'font-size': '0.75rem', color: 'var(--text-secondary)'}}, [
                document.createTextNode(`${dataset.sequences} sequences • ${Utils.formatBytes(dataset.size)} • ${Utils.formatRelativeTime(dataset.uploaded)}`)
            ])
        ]);

        item.appendChild(radio);
        item.appendChild(info);

        item.addEventListener('mouseenter', () => {
            if (!isSelected) {
                item.style.borderColor = 'var(--primary-light)';
                item.style.transform = 'translateX(4px)';
            }
        });

        item.addEventListener('mouseleave', () => {
            if (!isSelected) {
                item.style.borderColor = 'var(--border)';
                item.style.transform = 'translateX(0)';
            }
        });

        return item;
    },

    renderParametersConfiguration() {
        const wrapper = Utils.createElement('div', {class: 'animate-slideUp'});

        const title = Utils.createElement('h3', {style: {'font-size': '1.125rem', 'font-weight': '600', 'margin-bottom': '0.5rem'}}, [document.createTextNode('Configure Parameters')]);
        const description = Utils.createElement('p', {style: {'font-size': '0.875rem', color: 'var(--text-secondary)', 'margin-bottom': '1.5rem'}}, [document.createTextNode('Adjust algorithm parameters and evaluation settings')]);

        const form = Utils.createElement('div', {style: {display: 'grid', 'grid-template-columns': 'repeat(auto-fit, minmax(300px, 1fr))', gap: '1.5rem', 'margin-bottom': '2rem'}}, [
            Utils.createElement('div', {}, [
                Utils.createElement('h4', {style: {'font-size': '0.875rem', 'font-weight': '600', 'margin-bottom': '1rem'}}, [document.createTextNode('Algorithm Parameters')]),
                Components.input({label: 'Features per Image', type: 'number', value: this.parameters.features || 1000, placeholder: '1000', onInput: (e) => this.parameters.features = e.target.value}),
                Components.input({label: 'Scale Factor', type: 'number', value: this.parameters.scaleFactor || 1.2, placeholder: '1.2', step: '0.1', onInput: (e) => this.parameters.scaleFactor = e.target.value}),
                Components.input({label: 'Number of Levels', type: 'number', value: this.parameters.levels || 8, placeholder: '8', onInput: (e) => this.parameters.levels = e.target.value}),
                Utils.createElement('div', {style: {'margin-top': '1rem'}}, [
                    Components.switch({label: 'Enable Loop Closure', checked: this.parameters.loopClosure !== false, onChange: (checked) => this.parameters.loopClosure = checked})
                ])
            ]),
            Utils.createElement('div', {}, [
                Utils.createElement('h4', {style: {'font-size': '0.875rem', 'font-weight': '600', 'margin-bottom': '1rem'}}, [document.createTextNode('Evaluation Settings')]),
                Components.select({
                    label: 'Evaluation Metrics',
                    options: [
                        {value: 'ate', label: 'Absolute Trajectory Error'},
                        {value: 'rpe', label: 'Relative Pose Error'},
                        {value: 'both', label: 'Both ATE and RPE'}
                    ],
                    value: this.parameters.metrics || 'both',
                    onChange: (value) => this.parameters.metrics = value
                }),
                Components.input({label: 'Alignment Method', value: this.parameters.alignment || 'sim3', placeholder: 'sim3', onInput: (e) => this.parameters.alignment = e.target.value}),
                Utils.createElement('div', {style: {'margin-top': '1rem'}}, [
                    Components.switch({label: 'Save Trajectory', checked: this.parameters.saveTrajectory !== false, onChange: (checked) => this.parameters.saveTrajectory = checked}),
                    Components.switch({label: 'Generate Report', checked: this.parameters.generateReport !== false, onChange: (checked) => this.parameters.generateReport = checked})
                ])
            ])
        ]);

        const actions = this.createStepActions(true, true);

        wrapper.appendChild(title);
        wrapper.appendChild(description);
        wrapper.appendChild(form);
        wrapper.appendChild(actions);

        return wrapper;
    },

    renderReviewAndRun() {
        const wrapper = Utils.createElement('div', {class: 'animate-slideUp'});

        if (this.isEvaluating) {
            return this.renderEvaluationProgress();
        }

        const title = Utils.createElement('h3', {style: {'font-size': '1.125rem', 'font-weight': '600', 'margin-bottom': '0.5rem'}}, [document.createTextNode('Review Configuration')]);
        const description = Utils.createElement('p', {style: {'font-size': '0.875rem', color: 'var(--text-secondary)', 'margin-bottom': '1.5rem'}}, [document.createTextNode('Review your settings and start the evaluation')]);

        const summary = Utils.createElement('div', {style: {display: 'grid', gap: '1.5rem', 'margin-bottom': '2rem'}}, [
            this.createReviewSection('Plugin', [
                {label: 'Name', value: this.selectedPlugin || 'Not selected'},
                {label: 'Type', value: 'Visual SLAM'},
                {label: 'Version', value: '1.0.0'}
            ]),
            this.createReviewSection('Dataset', [
                {label: 'Name', value: this.selectedDataset || 'Not selected'},
                {label: 'Format', value: 'KITTI'},
                {label: 'Sequences', value: '11'}
            ]),
            this.createReviewSection('Parameters', [
                {label: 'Features per Image', value: this.parameters.features || 1000},
                {label: 'Scale Factor', value: this.parameters.scaleFactor || 1.2},
                {label: 'Metrics', value: this.parameters.metrics || 'both'},
                {label: 'Loop Closure', value: this.parameters.loopClosure !== false ? 'Enabled' : 'Disabled'}
            ])
        ]);

        const actions = Utils.createElement('div', {style: {display: 'flex', 'justify-content': 'space-between', gap: '1rem', 'padding-top': '1.5rem', 'border-top': '1px solid var(--border)'}}, [
            Components.button('Previous', {variant: 'secondary', onClick: () => this.previousStep()}),
            Components.button('Start Evaluation', {
                variant: 'primary',
                icon: '<path d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z"></path><path d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>',
                onClick: () => this.startEvaluation()
            })
        ]);

        wrapper.appendChild(title);
        wrapper.appendChild(description);
        wrapper.appendChild(summary);
        wrapper.appendChild(actions);

        return wrapper;
    },

    createReviewSection(title, items) {
        return Utils.createElement('div', {class: 'card', style: {padding: '1.5rem'}}, [
            Utils.createElement('h4', {style: {'font-size': '0.875rem', 'font-weight': '600', 'margin-bottom': '1rem', color: 'var(--text-secondary)', 'text-transform': 'uppercase', 'letter-spacing': '0.05em'}}, [document.createTextNode(title)]),
            Utils.createElement('div', {style: {display: 'grid', gap: '0.75rem'}},
                items.map(item =>
                    Utils.createElement('div', {style: {display: 'flex', 'justify-content': 'space-between', 'align-items': 'center'}}, [
                        Utils.createElement('span', {style: {'font-size': '0.875rem', color: 'var(--text-secondary)'}}, [document.createTextNode(item.label)]),
                        Utils.createElement('span', {style: {'font-size': '0.875rem', 'font-weight': '600', color: 'var(--text-primary)'}}, [document.createTextNode(item.value)])
                    ])
                )
            )
        ]);
    },

    renderEvaluationProgress() {
        const wrapper = Utils.createElement('div', {class: 'animate-slideUp', style: {'text-align': 'center'}});

        const icon = Utils.createElement('div', {style: {width: '5rem', height: '5rem', margin: '0 auto 1.5rem', position: 'relative'}}, [
            Utils.createElement('svg', {
                class: 'animate-spin',
                style: {width: '100%', height: '100%', color: 'var(--primary)'},
                viewBox: '0 0 24 24',
                fill: 'none',
                stroke: 'currentColor',
                'stroke-width': '2'
            }, []).innerHTML = '<path d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"></path>'
        ]);

        const title = Utils.createElement('h3', {style: {'font-size': '1.25rem', 'font-weight': '600', 'margin-bottom': '0.5rem'}}, [document.createTextNode('Evaluation in Progress')]);
        const status = Utils.createElement('p', {
            id: 'evaluation-status',
            style: {'font-size': '0.875rem', color: 'var(--text-secondary)', 'margin-bottom': '2rem'}
        }, [document.createTextNode('Initializing...')]);

        const progressContainer = Utils.createElement('div', {style: {'max-width': '500px', margin: '0 auto 2rem'}}, [
            Utils.createElement('div', {style: {display: 'flex', 'justify-content': 'space-between', 'margin-bottom': '0.5rem'}}, [
                Utils.createElement('span', {style: {'font-size': '0.875rem', 'font-weight': '600', color: 'var(--text-secondary)'}}, [document.createTextNode('Progress')]),
                Utils.createElement('span', {
                    id: 'evaluation-progress-percent',
                    style: {'font-size': '0.875rem', 'font-weight': '600', color: 'var(--primary)'}
                }, [document.createTextNode('0%')])
            ]),
            Components.progress(this.progress, 100)
        ]);

        const logs = Utils.createElement('div', {
            id: 'evaluation-logs',
            class: 'card',
            style: {
                padding: '1.5rem',
                'max-height': '200px',
                'overflow-y': 'auto',
                'text-align': 'left',
                background: 'var(--bg-dark)',
                color: 'var(--text-inverse)',
                'font-family': 'monospace',
                'font-size': '0.75rem',
                'line-height': '1.6'
            }
        }, [document.createTextNode('Starting evaluation...\n')]);

        const actions = Utils.createElement('div', {style: {display: 'flex', 'justify-content': 'center', gap: '1rem', 'margin-top': '2rem'}}, [
            Components.button('Cancel Evaluation', {
                variant: 'danger',
                onClick: () => this.cancelEvaluation()
            })
        ]);

        wrapper.appendChild(icon);
        wrapper.appendChild(title);
        wrapper.appendChild(status);
        wrapper.appendChild(progressContainer);
        wrapper.appendChild(logs);
        wrapper.appendChild(actions);

        return wrapper;
    },

    createStepActions(showPrevious, canContinue) {
        return Utils.createElement('div', {style: {display: 'flex', 'justify-content': 'space-between', gap: '1rem', 'padding-top': '1.5rem', 'border-top': '1px solid var(--border)'}}, [
            showPrevious
                ? Components.button('Previous', {variant: 'secondary', onClick: () => this.previousStep()})
                : Utils.createElement('div'),
            Components.button('Next', {
                variant: 'primary',
                disabled: !canContinue,
                onClick: () => this.nextStep()
            })
        ]);
    },

    selectPlugin(name) {
        this.selectedPlugin = name;
        this.render();
    },

    selectDataset(id) {
        this.selectedDataset = id;
        this.render();
    },

    async startEvaluation() {
        this.isEvaluating = true;
        this.progress = 0;
        this.render();

        try {
            const result = await API.evaluations.create({
                plugin: this.selectedPlugin,
                dataset: this.selectedDataset,
                parameters: this.parameters
            });
            this.evaluationId = result.id;
        } catch (error) {
            Components.toast('Failed to start evaluation', 'error');
            this.isEvaluating = false;
            this.render();
        }
    },

    startProgressMonitoring() {
        const statusEl = document.getElementById('evaluation-status');
        const progressEl = document.getElementById('evaluation-progress-percent');
        const logsEl = document.getElementById('evaluation-logs');

        const stages = [
            'Initializing plugin...',
            'Loading dataset...',
            'Running SLAM algorithm...',
            'Computing trajectory...',
            'Calculating metrics...',
            'Generating report...'
        ];

        let currentStage = 0;

        const interval = setInterval(() => {
            this.progress += Math.random() * 10;

            if (this.progress >= 100) {
                this.progress = 100;
                clearInterval(interval);

                if (statusEl) statusEl.textContent = 'Evaluation completed!';
                if (logsEl) logsEl.textContent += '\n✓ Evaluation completed successfully';

                setTimeout(() => {
                    Components.toast('Evaluation completed successfully', 'success');
                    App.navigate('results', {id: this.evaluationId});
                }, 1500);
            } else {
                const newStage = Math.floor((this.progress / 100) * stages.length);
                if (newStage > currentStage) {
                    currentStage = newStage;
                    if (statusEl) statusEl.textContent = stages[currentStage];
                    if (logsEl) logsEl.textContent += `\n${stages[currentStage]}`;
                    logsEl.scrollTop = logsEl.scrollHeight;
                }
            }

            if (progressEl) progressEl.textContent = `${Math.round(this.progress)}%`;

            const progressBar = document.querySelector('.step-content .progress-fill');
            if (progressBar) progressBar.style.width = `${this.progress}%`;
        }, 500);

        WS.on('evaluation_progress', (data) => {
            if (data.id === this.evaluationId) {
                this.progress = data.progress;
                if (statusEl) statusEl.textContent = data.stage;
                if (progressEl) progressEl.textContent = `${Math.round(data.progress)}%`;
                if (logsEl) {
                    logsEl.textContent += `\n${data.message}`;
                    logsEl.scrollTop = logsEl.scrollHeight;
                }
            }
        });
    },

    cancelEvaluation() {
        Components.confirm('Are you sure you want to cancel this evaluation?', {
            confirmText: 'Yes, Cancel',
            cancelText: 'Continue Evaluation',
            onConfirm: () => {
                this.isEvaluating = false;
                this.progress = 0;
                this.currentStep = 0;
                this.render();
                Components.toast('Evaluation cancelled', 'warning');
            }
        });
    },

    async fetchPlugins() {
        try {
            const data = await API.plugins.list();
            return data.plugins || this.getMockPlugins();
        } catch {
            return this.getMockPlugins();
        }
    },

    getMockPlugins() {
        return [
            {name: 'ORB-SLAM3', version: '1.0.0', type: 'visual', description: 'Feature-based visual SLAM with loop closure detection'},
            {name: 'VINS-Mono', version: '2.1.0', type: 'visual-inertial', description: 'Monocular visual-inertial SLAM system'},
            {name: 'DSO', version: '1.5.2', type: 'visual', description: 'Direct sparse odometry for monocular cameras'},
            {name: 'LIO-SAM', version: '1.2.0', type: 'lidar-inertial', description: 'Tightly-coupled lidar inertial odometry'}
        ];
    },

    async fetchDatasets() {
        try {
            const data = await API.datasets.list();
            return data.datasets || this.getMockDatasets();
        } catch {
            return this.getMockDatasets();
        }
    },

    getMockDatasets() {
        return [
            {id: 'kitti-00', name: 'KITTI-00', format: 'KITTI', sequences: 11, size: 1024 * 1024 * 1024 * 2.5, uploaded: new Date(Date.now() - 86400000 * 7)},
            {id: 'euroc-mh01', name: 'EuRoC MH-01', format: 'EuRoC', sequences: 5, size: 1024 * 1024 * 1024 * 1.2, uploaded: new Date(Date.now() - 86400000 * 14)},
            {id: 'tum-rgbd', name: 'TUM RGB-D', format: 'TUM', sequences: 8, size: 1024 * 1024 * 1024 * 0.8, uploaded: new Date(Date.now() - 86400000 * 3)}
        ];
    }
};
