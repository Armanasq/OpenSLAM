const DatasetsView = {
    datasets: [],
    uploadProgress: {},
    dragCounter: 0,

    async render() {
        const container = document.getElementById('view-datasets');
        container.innerHTML = '';

        await this.loadDatasets();

        const header = Utils.createElement('div', {style: {display: 'flex', 'justify-content': 'space-between', 'align-items': 'center', 'margin-bottom': '2rem'}}, [
            Utils.createElement('div', {}, [
                Utils.createElement('h2', {style: {'font-size': '1.5rem', 'font-weight': '700', color: 'var(--text-primary)', 'margin-bottom': '0.25rem'}}, [document.createTextNode('Datasets')]),
                Utils.createElement('p', {style: {'font-size': '0.875rem', color: 'var(--text-secondary)'}}, [
                    document.createTextNode(`${this.datasets.length} datasets • ${Utils.formatBytes(this.getTotalSize())} total`)
                ])
            ]),
            Components.button('Upload Dataset', {
                variant: 'primary',
                icon: '<path d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"></path>',
                onClick: () => this.showUploadModal()
            })
        ]);

        const dropZone = this.createDropZone();
        const grid = this.createDatasetsGrid();

        container.appendChild(header);
        container.appendChild(dropZone);
        container.appendChild(grid);

        this.setupDragAndDrop(dropZone);
    },

    async loadDatasets() {
        try {
            const data = await API.datasets.list();
            this.datasets = data.datasets || this.getMockDatasets();
        } catch {
            this.datasets = this.getMockDatasets();
        }
    },

    getMockDatasets() {
        return [
            {id: '1', name: 'KITTI-00', format: 'KITTI', sequences: 11, frames: 4540, size: 1024 * 1024 * 1024 * 2.5, uploaded: new Date(Date.now() - 86400000 * 7), status: 'ready'},
            {id: '2', name: 'EuRoC MH-01', format: 'EuRoC', sequences: 5, frames: 3682, size: 1024 * 1024 * 1024 * 1.2, uploaded: new Date(Date.now() - 86400000 * 14), status: 'ready'},
            {id: '3', name: 'TUM RGB-D', format: 'TUM', sequences: 8, frames: 2912, size: 1024 * 1024 * 1024 * 0.8, uploaded: new Date(Date.now() - 86400000 * 3), status: 'ready'},
            {id: '4', name: 'KITTI-05', format: 'KITTI', sequences: 11, frames: 2761, size: 1024 * 1024 * 1024 * 1.8, uploaded: new Date(Date.now() - 86400000 * 21), status: 'ready'},
            {id: '5', name: 'Custom Dataset', format: 'Custom', sequences: 3, frames: 1523, size: 1024 * 1024 * 512, uploaded: new Date(Date.now() - 86400000 * 2), status: 'processing'}
        ];
    },

    getTotalSize() {
        return this.datasets.reduce((sum, d) => sum + d.size, 0);
    },

    createDropZone() {
        const dropZone = Utils.createElement('div', {
            id: 'drop-zone',
            class: 'drop-zone card',
            style: {
                padding: '3rem',
                'text-align': 'center',
                border: '2px dashed var(--border)',
                'border-radius': 'var(--radius-xl)',
                'margin-bottom': '2rem',
                background: 'var(--bg-secondary)',
                cursor: 'pointer',
                transition: 'all var(--duration-normal) var(--ease)',
                position: 'relative',
                overflow: 'hidden'
            }
        });

        const icon = Utils.createElement('svg', {
            style: {
                width: '4rem',
                height: '4rem',
                color: 'var(--text-tertiary)',
                margin: '0 auto 1rem',
                transition: 'all var(--duration-normal) var(--ease-spring)'
            },
            viewBox: '0 0 24 24',
            fill: 'none',
            stroke: 'currentColor',
            'stroke-width': '2'
        });
        icon.innerHTML = '<path d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"></path>';

        const title = Utils.createElement('h3', {
            style: {
                'font-size': '1.125rem',
                'font-weight': '600',
                'margin-bottom': '0.5rem',
                color: 'var(--text-primary)'
            }
        }, [document.createTextNode('Drop files here or click to upload')]);

        const description = Utils.createElement('p', {
            style: {
                'font-size': '0.875rem',
                color: 'var(--text-secondary)',
                'margin-bottom': '1rem'
            }
        }, [document.createTextNode('Support for .bag, .csv, .txt, .yaml files (max 100MB)')]);

        const button = Components.button('Browse Files', {
            variant: 'secondary',
            size: 'sm'
        });

        dropZone.appendChild(icon);
        dropZone.appendChild(title);
        dropZone.appendChild(description);
        dropZone.appendChild(button);

        dropZone.addEventListener('click', () => {
            const input = document.createElement('input');
            input.type = 'file';
            input.multiple = true;
            input.accept = CONFIG.FILE.ALLOWED_TYPES.join(',');
            input.onchange = (e) => this.handleFiles(e.target.files);
            input.click();
        });

        dropZone.addEventListener('mouseenter', () => {
            dropZone.style.borderColor = 'var(--primary)';
            dropZone.style.background = 'rgba(37, 99, 235, 0.05)';
            icon.style.color = 'var(--primary)';
            icon.style.transform = 'translateY(-8px)';
        });

        dropZone.addEventListener('mouseleave', () => {
            if (this.dragCounter === 0) {
                dropZone.style.borderColor = 'var(--border)';
                dropZone.style.background = 'var(--bg-secondary)';
                icon.style.color = 'var(--text-tertiary)';
                icon.style.transform = 'translateY(0)';
            }
        });

        return dropZone;
    },

    setupDragAndDrop(dropZone) {
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            document.body.addEventListener(eventName, (e) => {
                e.preventDefault();
                e.stopPropagation();
            });
        });

        document.body.addEventListener('dragenter', (e) => {
            this.dragCounter++;
            if (e.dataTransfer.types.includes('Files')) {
                dropZone.style.borderColor = 'var(--primary)';
                dropZone.style.background = 'rgba(37, 99, 235, 0.1)';
                dropZone.style.transform = 'scale(1.02)';
                const icon = dropZone.querySelector('svg');
                if (icon) {
                    icon.style.color = 'var(--primary)';
                    icon.style.transform = 'translateY(-8px) scale(1.1)';
                }
            }
        });

        document.body.addEventListener('dragleave', () => {
            this.dragCounter--;
            if (this.dragCounter === 0) {
                dropZone.style.borderColor = 'var(--border)';
                dropZone.style.background = 'var(--bg-secondary)';
                dropZone.style.transform = 'scale(1)';
                const icon = dropZone.querySelector('svg');
                if (icon) {
                    icon.style.color = 'var(--text-tertiary)';
                    icon.style.transform = 'translateY(0) scale(1)';
                }
            }
        });

        document.body.addEventListener('drop', (e) => {
            this.dragCounter = 0;
            dropZone.style.borderColor = 'var(--border)';
            dropZone.style.background = 'var(--bg-secondary)';
            dropZone.style.transform = 'scale(1)';
            const icon = dropZone.querySelector('svg');
            if (icon) {
                icon.style.color = 'var(--text-tertiary)';
                icon.style.transform = 'translateY(0) scale(1)';
            }

            const files = e.dataTransfer.files;
            if (files.length > 0) {
                this.handleFiles(files);
            }
        });
    },

    handleFiles(files) {
        Array.from(files).forEach(file => {
            if (file.size > CONFIG.FILE.MAX_SIZE) {
                Components.toast(`File ${file.name} exceeds maximum size of ${Utils.formatBytes(CONFIG.FILE.MAX_SIZE)}`, 'error');
                return;
            }

            const extension = '.' + file.name.split('.').pop();
            if (!CONFIG.FILE.ALLOWED_TYPES.includes(extension)) {
                Components.toast(`File type ${extension} is not supported`, 'error');
                return;
            }

            this.uploadFile(file);
        });
    },

    async uploadFile(file) {
        const uploadId = Date.now() + '-' + Math.random();
        this.uploadProgress[uploadId] = {
            name: file.name,
            size: file.size,
            progress: 0,
            status: 'uploading'
        };

        this.showUploadProgress();

        try {
            await API.upload('/datasets', file, (progress) => {
                this.uploadProgress[uploadId].progress = progress;
                this.updateUploadProgress(uploadId);
            });

            this.uploadProgress[uploadId].status = 'completed';
            this.updateUploadProgress(uploadId);

            Components.toast(`${file.name} uploaded successfully`, 'success');

            setTimeout(() => {
                delete this.uploadProgress[uploadId];
                if (Object.keys(this.uploadProgress).length === 0) {
                    this.hideUploadProgress();
                }
                this.loadDatasets().then(() => this.render());
            }, 2000);
        } catch (error) {
            this.uploadProgress[uploadId].status = 'failed';
            this.updateUploadProgress(uploadId);
            Components.toast(`Failed to upload ${file.name}`, 'error');
        }
    },

    showUploadProgress() {
        let modal = document.getElementById('upload-progress-modal');
        if (!modal) {
            modal = Utils.createElement('div', {
                id: 'upload-progress-modal',
                class: 'card animate-slideUp',
                style: {
                    position: 'fixed',
                    bottom: '2rem',
                    right: '2rem',
                    width: '400px',
                    padding: '1.5rem',
                    'z-index': '1060',
                    'box-shadow': 'var(--shadow-xl)'
                }
            });

            const header = Utils.createElement('div', {style: {display: 'flex', 'justify-content': 'space-between', 'align-items': 'center', 'margin-bottom': '1rem'}}, [
                Utils.createElement('h4', {style: {'font-size': '1rem', 'font-weight': '600'}}, [document.createTextNode('Uploading Files')]),
                Utils.createElement('button', {
                    style: {
                        background: 'none',
                        border: 'none',
                        cursor: 'pointer',
                        color: 'var(--text-secondary)',
                        padding: '0.25rem'
                    },
                    onclick: () => this.hideUploadProgress()
                }, [
                    Utils.createElement('svg', {style: {width: '1.25rem', height: '1.25rem'}, viewBox: '0 0 24 24', fill: 'none', stroke: 'currentColor', 'stroke-width': '2'}, []).innerHTML = '<path d="M6 18L18 6M6 6l12 12"></path>'
                ])
            ]);

            const list = Utils.createElement('div', {id: 'upload-progress-list', style: {display: 'flex', 'flex-direction': 'column', gap: '0.75rem'}});

            modal.appendChild(header);
            modal.appendChild(list);
            document.body.appendChild(modal);
        }

        this.updateUploadProgress();
    },

    updateUploadProgress(uploadId = null) {
        const list = document.getElementById('upload-progress-list');
        if (!list) return;

        if (uploadId) {
            const existing = document.getElementById(`upload-${uploadId}`);
            if (existing) {
                const upload = this.uploadProgress[uploadId];
                const progressBar = existing.querySelector('.progress-fill');
                const statusIcon = existing.querySelector('.status-icon');

                if (progressBar) progressBar.style.width = `${upload.progress}%`;

                if (statusIcon) {
                    if (upload.status === 'completed') {
                        statusIcon.innerHTML = '<path d="M5 13l4 4L19 7"></path>';
                        statusIcon.style.color = 'var(--success)';
                    } else if (upload.status === 'failed') {
                        statusIcon.innerHTML = '<path d="M6 18L18 6M6 6l12 12"></path>';
                        statusIcon.style.color = 'var(--error)';
                    }
                }
            }
        } else {
            list.innerHTML = '';

            Object.entries(this.uploadProgress).forEach(([id, upload]) => {
                const item = Utils.createElement('div', {id: `upload-${id}`, style: {padding: '0.75rem', background: 'var(--bg-tertiary)', 'border-radius': 'var(--radius-lg)'}}, [
                    Utils.createElement('div', {style: {display: 'flex', 'justify-content': 'space-between', 'align-items': 'center', 'margin-bottom': '0.5rem'}}, [
                        Utils.createElement('div', {style: {flex: '1', 'min-width': '0'}}, [
                            Utils.createElement('div', {style: {'font-size': '0.875rem', 'font-weight': '500', 'white-space': 'nowrap', overflow: 'hidden', 'text-overflow': 'ellipsis'}}, [document.createTextNode(upload.name)]),
                            Utils.createElement('div', {style: {'font-size': '0.75rem', color: 'var(--text-tertiary)'}}, [document.createTextNode(Utils.formatBytes(upload.size))])
                        ]),
                        Utils.createElement('svg', {
                            class: 'status-icon',
                            style: {
                                width: '1.25rem',
                                height: '1.25rem',
                                color: upload.status === 'uploading' ? 'var(--primary)' : upload.status === 'completed' ? 'var(--success)' : 'var(--error)',
                                'flex-shrink': '0',
                                'margin-left': '0.5rem'
                            },
                            viewBox: '0 0 24 24',
                            fill: 'none',
                            stroke: 'currentColor',
                            'stroke-width': '2'
                        }, []).innerHTML = upload.status === 'uploading' ? '<path d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"></path>' : upload.status === 'completed' ? '<path d="M5 13l4 4L19 7"></path>' : '<path d="M6 18L18 6M6 6l12 12"></path>'
                    ]),
                    Utils.createElement('div', {style: {height: '4px', background: 'var(--bg-primary)', 'border-radius': 'var(--radius-full)', overflow: 'hidden'}}, [
                        Utils.createElement('div', {
                            class: 'progress-fill',
                            style: {
                                height: '100%',
                                width: `${upload.progress}%`,
                                background: upload.status === 'failed' ? 'var(--error)' : 'linear-gradient(90deg, var(--primary), var(--primary-light))',
                                'border-radius': 'var(--radius-full)',
                                transition: 'width var(--duration-normal) var(--ease)'
                            }
                        })
                    ])
                ]);

                if (upload.status === 'uploading') {
                    const spinner = item.querySelector('.status-icon');
                    if (spinner) spinner.classList.add('animate-spin');
                }

                list.appendChild(item);
            });
        }
    },

    hideUploadProgress() {
        const modal = document.getElementById('upload-progress-modal');
        if (modal) {
            modal.remove();
        }
    },

    createDatasetsGrid() {
        if (this.datasets.length === 0) {
            return Components.emptyState({
                icon: '<path d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2z"></path>',
                title: 'No Datasets Yet',
                description: 'Upload your first dataset to get started'
            });
        }

        return Utils.createElement('div', {
            class: 'stagger-fadeIn',
            style: {
                display: 'grid',
                'grid-template-columns': 'repeat(auto-fill, minmax(320px, 1fr))',
                gap: '1.5rem'
            }
        }, this.datasets.map((dataset, index) => this.createDatasetCard(dataset, index)));
    },

    createDatasetCard(dataset, index) {
        const card = Utils.createElement('div', {
            class: 'dataset-card card hover-lift',
            style: {
                padding: '1.5rem',
                cursor: 'pointer',
                position: 'relative',
                'animation-delay': `${index * 50}ms`
            },
            onclick: () => this.showDatasetDetails(dataset)
        });

        const statusBadge = Utils.createElement('div', {
            style: {
                position: 'absolute',
                top: '1rem',
                right: '1rem'
            }
        }, [Components.badge(dataset.status, dataset.status === 'ready' ? 'success' : 'warning')]);

        const icon = Utils.createElement('div', {
            style: {
                width: '3.5rem',
                height: '3.5rem',
                'border-radius': 'var(--radius-xl)',
                background: 'linear-gradient(135deg, var(--primary), var(--primary-light))',
                display: 'flex',
                'align-items': 'center',
                'justify-content': 'center',
                'margin-bottom': '1rem'
            }
        }, [
            Utils.createElement('svg', {style: {width: '2rem', height: '2rem', color: 'var(--text-inverse)'}, viewBox: '0 0 24 24', fill: 'none', stroke: 'currentColor', 'stroke-width': '2'}, []).innerHTML = '<path d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2z"></path><path d="M3 7h18M9 3v4m6-4v4"></path>'
        ]);

        const header = Utils.createElement('div', {style: {'margin-bottom': '1rem'}}, [
            Utils.createElement('h3', {style: {'font-size': '1.125rem', 'font-weight': '600', 'margin-bottom': '0.25rem'}}, [document.createTextNode(dataset.name)]),
            Utils.createElement('div', {style: {display: 'flex', gap: '0.5rem'}}, [
                Components.tag(dataset.format)
            ])
        ]);

        const stats = Utils.createElement('div', {style: {display: 'grid', 'grid-template-columns': 'repeat(2, 1fr)', gap: '0.75rem', 'margin-bottom': '1rem'}}, [
            this.createStatItem('Sequences', dataset.sequences),
            this.createStatItem('Frames', Utils.formatNumber(dataset.frames)),
            this.createStatItem('Size', Utils.formatBytes(dataset.size)),
            this.createStatItem('Uploaded', Utils.formatRelativeTime(dataset.uploaded))
        ]);

        const actions = Utils.createElement('div', {style: {display: 'flex', gap: '0.5rem', 'padding-top': '1rem', 'border-top': '1px solid var(--border)'}}, [
            Components.button('Evaluate', {
                variant: 'primary',
                size: 'sm',
                onClick: (e) => {
                    e.stopPropagation();
                    App.navigate('evaluate', {dataset: dataset.id});
                }
            }),
            Components.button('Delete', {
                variant: 'danger',
                size: 'sm',
                onClick: (e) => {
                    e.stopPropagation();
                    this.deleteDataset(dataset);
                }
            })
        ]);

        card.appendChild(statusBadge);
        card.appendChild(icon);
        card.appendChild(header);
        card.appendChild(stats);
        card.appendChild(actions);

        return card;
    },

    createStatItem(label, value) {
        return Utils.createElement('div', {style: {padding: '0.5rem', background: 'var(--bg-tertiary)', 'border-radius': 'var(--radius-md)', 'text-align': 'center'}}, [
            Utils.createElement('div', {style: {'font-size': '0.875rem', 'font-weight': '600', color: 'var(--text-primary)', 'margin-bottom': '0.25rem'}}, [document.createTextNode(value)]),
            Utils.createElement('div', {style: {'font-size': '0.75rem', color: 'var(--text-tertiary)'}}, [document.createTextNode(label)])
        ]);
    },

    showDatasetDetails(dataset) {
        const content = Utils.createElement('div', {}, [
            Utils.createElement('div', {style: {display: 'grid', 'grid-template-columns': 'repeat(2, 1fr)', gap: '1.5rem', 'margin-bottom': '2rem'}}, [
                Utils.createElement('div', {}, [
                    Utils.createElement('h4', {style: {'font-size': '0.875rem', 'font-weight': '600', 'margin-bottom': '1rem', color: 'var(--text-secondary)', 'text-transform': 'uppercase', 'letter-spacing': '0.05em'}}, [document.createTextNode('Dataset Information')]),
                    Utils.createElement('div', {style: {display: 'grid', gap: '0.75rem'}}, [
                        this.createDetailRow('Name', dataset.name),
                        this.createDetailRow('Format', dataset.format),
                        this.createDetailRow('Status', Components.badge(dataset.status, dataset.status === 'ready' ? 'success' : 'warning')),
                        this.createDetailRow('Sequences', dataset.sequences),
                        this.createDetailRow('Total Frames', Utils.formatNumber(dataset.frames))
                    ])
                ]),
                Utils.createElement('div', {}, [
                    Utils.createElement('h4', {style: {'font-size': '0.875rem', 'font-weight': '600', 'margin-bottom': '1rem', color: 'var(--text-secondary)', 'text-transform': 'uppercase', 'letter-spacing': '0.05em'}}, [document.createTextNode('Storage')]),
                    Utils.createElement('div', {style: {display: 'grid', gap: '0.75rem'}}, [
                        this.createDetailRow('Size', Utils.formatBytes(dataset.size)),
                        this.createDetailRow('Uploaded', Utils.formatDateTime(dataset.uploaded)),
                        this.createDetailRow('Last Accessed', Utils.formatRelativeTime(dataset.uploaded))
                    ])
                ])
            ]),
            Utils.createElement('div', {}, [
                Utils.createElement('h4', {style: {'font-size': '0.875rem', 'font-weight': '600', 'margin-bottom': '1rem', color: 'var(--text-secondary)', 'text-transform': 'uppercase', 'letter-spacing': '0.05em'}}, [document.createTextNode('Dataset Preview')]),
                Utils.createElement('div', {class: 'card', style: {padding: '2rem', 'text-align': 'center', background: 'var(--bg-tertiary)'}}, [
                    Utils.createElement('svg', {style: {width: '3rem', height: '3rem', color: 'var(--text-tertiary)', margin: '0 auto 1rem'}, viewBox: '0 0 24 24', fill: 'none', stroke: 'currentColor', 'stroke-width': '2'}, []).innerHTML = '<path d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"></path>',
                    Utils.createElement('p', {style: {'font-size': '0.875rem', color: 'var(--text-secondary)'}}, [document.createTextNode('Dataset preview will be available soon')])
                ])
            ])
        ]);

        Components.modal(dataset.name, content, {
            size: 'large',
            actions: [
                {label: 'Delete', variant: 'danger', onClick: () => this.deleteDataset(dataset)},
                {label: 'Evaluate', variant: 'primary', onClick: () => App.navigate('evaluate', {dataset: dataset.id})}
            ]
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

    deleteDataset(dataset) {
        Components.confirm(`Are you sure you want to delete "${dataset.name}"? This action cannot be undone.`, {
            confirmText: 'Delete',
            cancelText: 'Cancel',
            variant: 'danger',
            onConfirm: async () => {
                try {
                    await API.datasets.delete(dataset.id);
                    Components.toast(`${dataset.name} deleted successfully`, 'success');
                    await this.loadDatasets();
                    this.render();
                } catch (error) {
                    Components.toast(`Failed to delete ${dataset.name}`, 'error');
                }
            }
        });
    },

    showUploadModal() {
        const content = Utils.createElement('div', {}, [
            Utils.createElement('p', {style: {'font-size': '0.875rem', color: 'var(--text-secondary)', 'margin-bottom': '1.5rem'}}, [document.createTextNode('Upload a new dataset for SLAM evaluation')]),
            Components.input({label: 'Dataset Name', placeholder: 'my-dataset'}),
            Components.select({
                label: 'Dataset Format',
                options: [
                    {value: 'kitti', label: 'KITTI'},
                    {value: 'euroc', label: 'EuRoC'},
                    {value: 'tum', label: 'TUM RGB-D'},
                    {value: 'custom', label: 'Custom Format'}
                ]
            }),
            Components.fileUpload({
                label: 'Dataset Files',
                accept: CONFIG.FILE.ALLOWED_TYPES.join(','),
                multiple: true
            })
        ]);

        Components.modal('Upload Dataset', content, {
            actions: [
                {label: 'Cancel', variant: 'secondary'},
                {
                    label: 'Upload',
                    variant: 'primary',
                    onClick: () => {
                        Components.toast('Dataset upload started', 'success');
                    }
                }
            ]
        });
    }
};
