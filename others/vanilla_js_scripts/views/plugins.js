const PluginsView = {
    viewMode: 'grid',
    searchQuery: '',
    filterType: 'all',
    sortBy: 'name',
    plugins: [],

    async render() {
        const container = document.getElementById('view-plugins');
        container.innerHTML = '';

        await this.loadPlugins();

        const header = Utils.createElement('div', {style: {display: 'flex', 'justify-content': 'space-between', 'align-items': 'center', 'margin-bottom': '2rem'}}, [
            Utils.createElement('div', {}, [
                Utils.createElement('h2', {style: {'font-size': '1.5rem', 'font-weight': '700', color: 'var(--text-primary)', 'margin-bottom': '0.25rem'}}, [document.createTextNode('SLAM Plugins')]),
                Utils.createElement('p', {style: {'font-size': '0.875rem', color: 'var(--text-secondary)'}}, [document.createTextNode(`${this.plugins.length} plugins available`)])
            ]),
            Utils.createElement('div', {style: {display: 'flex', gap: '0.75rem'}}, [
                this.createViewToggle(),
                Components.button('Add Plugin', {variant: 'primary', icon: '<path d="M12 4v16m8-8H4"></path>', onClick: () => this.showAddPluginModal()})
            ])
        ]);

        const toolbar = Utils.createElement('div', {class: 'plugins-toolbar', style: {display: 'flex', gap: '1rem', 'margin-bottom': '1.5rem', 'flex-wrap': 'wrap'}}, [
            this.createSearchInput(),
            this.createFilterDropdown(),
            this.createSortDropdown()
        ]);

        const pluginsContainer = Utils.createElement('div', {
            class: `plugins-${this.viewMode} stagger-fadeIn`,
            style: this.viewMode === 'grid'
                ? {display: 'grid', 'grid-template-columns': 'repeat(auto-fill, minmax(320px, 1fr))', gap: '1.5rem'}
                : {display: 'flex', 'flex-direction': 'column', gap: '1rem'}
        });

        const filteredPlugins = this.filterAndSortPlugins();

        if (filteredPlugins.length === 0) {
            pluginsContainer.appendChild(Components.emptyState({
                icon: '<path d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4"></path>',
                title: 'No Plugins Found',
                description: this.searchQuery ? 'Try adjusting your search or filters' : 'Get started by adding your first plugin'
            }));
        } else {
            filteredPlugins.forEach((plugin, index) => {
                const card = this.viewMode === 'grid'
                    ? this.createPluginCard(plugin, index)
                    : this.createPluginListItem(plugin, index);
                pluginsContainer.appendChild(card);
            });
        }

        container.appendChild(header);
        container.appendChild(toolbar);
        container.appendChild(pluginsContainer);
    },

    async loadPlugins() {
        try {
            const data = await API.plugins.list();
            this.plugins = data.plugins || this.getMockPlugins();
        } catch {
            this.plugins = this.getMockPlugins();
        }
    },

    getMockPlugins() {
        return [
            {name: 'ORB-SLAM3', version: '1.0.0', type: 'visual', status: 'active', inputTypes: ['image', 'stereo'], description: 'Feature-based visual SLAM with loop closure detection', author: 'UZ Research', downloads: 1243, rating: 4.8, lastUpdated: new Date(Date.now() - 86400000 * 5)},
            {name: 'VINS-Mono', version: '2.1.0', type: 'visual-inertial', status: 'active', inputTypes: ['image', 'imu'], description: 'Monocular visual-inertial SLAM system', author: 'HKUST', downloads: 892, rating: 4.6, lastUpdated: new Date(Date.now() - 86400000 * 12)},
            {name: 'DSO', version: '1.5.2', type: 'visual', status: 'active', inputTypes: ['image'], description: 'Direct sparse odometry for monocular cameras', author: 'TUM', downloads: 567, rating: 4.5, lastUpdated: new Date(Date.now() - 86400000 * 20)},
            {name: 'LIO-SAM', version: '1.2.0', type: 'lidar-inertial', status: 'active', inputTypes: ['lidar', 'imu'], description: 'Tightly-coupled lidar inertial odometry via smoothing and mapping', author: 'RoboticsLab', downloads: 734, rating: 4.7, lastUpdated: new Date(Date.now() - 86400000 * 8)},
            {name: 'Cartographer', version: '3.0.1', type: 'lidar', status: 'active', inputTypes: ['lidar'], description: 'Real-time simultaneous localization and mapping', author: 'Google', downloads: 1567, rating: 4.9, lastUpdated: new Date(Date.now() - 86400000 * 3)},
            {name: 'OpenVSLAM', version: '0.9.0', type: 'visual', status: 'beta', inputTypes: ['image'], description: 'Versatile visual SLAM framework', author: 'Community', downloads: 423, rating: 4.3, lastUpdated: new Date(Date.now() - 86400000 * 30)}
        ];
    },

    createViewToggle() {
        const toggle = Utils.createElement('div', {class: 'view-toggle', style: {display: 'flex', background: 'var(--bg-tertiary)', 'border-radius': 'var(--radius-lg)', padding: '0.25rem'}}, [
            this.createViewToggleButton('grid', '<path d="M4 5a1 1 0 011-1h4a1 1 0 011 1v4a1 1 0 01-1 1H5a1 1 0 01-1-1V5zM14 5a1 1 0 011-1h4a1 1 0 011 1v4a1 1 0 01-1 1h-4a1 1 0 01-1-1V5zM4 15a1 1 0 011-1h4a1 1 0 011 1v4a1 1 0 01-1 1H5a1 1 0 01-1-1v-4zM14 15a1 1 0 011-1h4a1 1 0 011 1v4a1 1 0 01-1 1h-4a1 1 0 01-1-1v-4z"></path>'),
            this.createViewToggleButton('list', '<path d="M4 6h16M4 12h16M4 18h16"></path>')
        ]);
        return toggle;
    },

    createViewToggleButton(mode, icon) {
        const isActive = this.viewMode === mode;
        const btn = Utils.createElement('button', {
            class: isActive ? 'active' : '',
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
            onclick: () => this.changeViewMode(mode)
        }, [
            Utils.createElement('svg', {style: {width: '1.25rem', height: '1.25rem'}, viewBox: '0 0 24 24', fill: 'none', stroke: 'currentColor', 'stroke-width': '2'}, []).innerHTML = icon
        ]);

        btn.addEventListener('mouseenter', () => {
            if (!isActive) {
                btn.style.background = 'var(--bg-secondary)';
                btn.style.color = 'var(--text-primary)';
            }
        });

        btn.addEventListener('mouseleave', () => {
            if (!isActive) {
                btn.style.background = 'transparent';
                btn.style.color = 'var(--text-secondary)';
            }
        });

        return btn;
    },

    changeViewMode(mode) {
        this.viewMode = mode;
        this.render();
    },

    createSearchInput() {
        const searchContainer = Utils.createElement('div', {style: {position: 'relative', flex: '1', 'min-width': '300px'}});

        const icon = Utils.createElement('svg', {
            style: {
                position: 'absolute',
                left: '1rem',
                top: '50%',
                transform: 'translateY(-50%)',
                width: '1.25rem',
                height: '1.25rem',
                color: 'var(--text-tertiary)',
                'pointer-events': 'none'
            },
            viewBox: '0 0 24 24',
            fill: 'none',
            stroke: 'currentColor',
            'stroke-width': '2'
        });
        icon.innerHTML = '<circle cx="11" cy="11" r="8"></circle><path d="M21 21l-4.35-4.35"></path>';

        const input = Components.input({
            placeholder: 'Search plugins...',
            value: this.searchQuery,
            style: {
                'padding-left': '3rem',
                width: '100%'
            },
            onInput: Utils.debounce((e) => {
                this.searchQuery = e.target.value;
                this.render();
            }, CONFIG.DEBOUNCE_DELAY)
        });

        searchContainer.appendChild(icon);
        searchContainer.appendChild(input);
        return searchContainer;
    },

    createFilterDropdown() {
        const options = [
            {value: 'all', label: 'All Types'},
            {value: 'visual', label: 'Visual'},
            {value: 'visual-inertial', label: 'Visual-Inertial'},
            {value: 'lidar', label: 'LiDAR'},
            {value: 'lidar-inertial', label: 'LiDAR-Inertial'}
        ];

        return Components.select({
            options: options,
            value: this.filterType,
            onChange: (value) => {
                this.filterType = value;
                this.render();
            },
            style: {'min-width': '180px'}
        });
    },

    createSortDropdown() {
        const options = [
            {value: 'name', label: 'Sort by Name'},
            {value: 'downloads', label: 'Sort by Downloads'},
            {value: 'rating', label: 'Sort by Rating'},
            {value: 'updated', label: 'Sort by Updated'}
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

    filterAndSortPlugins() {
        let filtered = this.plugins;

        if (this.searchQuery) {
            const query = this.searchQuery.toLowerCase();
            filtered = filtered.filter(p =>
                p.name.toLowerCase().includes(query) ||
                p.description.toLowerCase().includes(query) ||
                p.author.toLowerCase().includes(query)
            );
        }

        if (this.filterType !== 'all') {
            filtered = filtered.filter(p => p.type === this.filterType);
        }

        filtered.sort((a, b) => {
            switch (this.sortBy) {
                case 'downloads': return b.downloads - a.downloads;
                case 'rating': return b.rating - a.rating;
                case 'updated': return b.lastUpdated - a.lastUpdated;
                default: return a.name.localeCompare(b.name);
            }
        });

        return filtered;
    },

    createPluginCard(plugin, index) {
        const card = Utils.createElement('div', {
            class: 'plugin-card card hover-lift',
            style: {
                padding: '1.5rem',
                cursor: 'pointer',
                position: 'relative',
                overflow: 'hidden',
                'animation-delay': `${index * 50}ms`
            }
        });

        const statusBadge = Utils.createElement('div', {
            style: {
                position: 'absolute',
                top: '1rem',
                right: '1rem'
            }
        }, [Components.badge(plugin.status, plugin.status === 'active' ? 'success' : 'warning')]);

        const header = Utils.createElement('div', {style: {display: 'flex', 'align-items': 'flex-start', gap: '1rem', 'margin-bottom': '1rem'}}, [
            this.createPluginIcon(plugin.type),
            Utils.createElement('div', {style: {flex: '1', 'min-width': '0'}}, [
                Utils.createElement('h3', {style: {'font-size': '1.125rem', 'font-weight': '600', color: 'var(--text-primary)', 'margin-bottom': '0.25rem', 'white-space': 'nowrap', overflow: 'hidden', 'text-overflow': 'ellipsis'}}, [document.createTextNode(plugin.name)]),
                Utils.createElement('div', {style: {'font-size': '0.75rem', color: 'var(--text-tertiary)'}}, [document.createTextNode(`v${plugin.version} • ${plugin.author}`)])
            ])
        ]);

        const description = Utils.createElement('p', {
            style: {
                'font-size': '0.875rem',
                color: 'var(--text-secondary)',
                'line-height': '1.5',
                'margin-bottom': '1rem',
                display: '-webkit-box',
                '-webkit-line-clamp': '2',
                '-webkit-box-orient': 'vertical',
                overflow: 'hidden'
            }
        }, [document.createTextNode(plugin.description)]);

        const tags = Utils.createElement('div', {style: {display: 'flex', gap: '0.5rem', 'flex-wrap': 'wrap', 'margin-bottom': '1rem'}},
            plugin.inputTypes.map(type => Components.tag(type))
        );

        const stats = Utils.createElement('div', {style: {display: 'flex', 'justify-content': 'space-between', 'align-items': 'center', 'padding-top': '1rem', 'border-top': '1px solid var(--border)'}}, [
            Utils.createElement('div', {style: {display: 'flex', gap: '1rem'}}, [
                this.createStat('<path d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"></path>', Utils.formatNumber(plugin.downloads)),
                this.createStat('<path d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z"></path>', plugin.rating.toFixed(1))
            ]),
            Utils.createElement('div', {style: {'font-size': '0.75rem', color: 'var(--text-tertiary)'}}, [document.createTextNode(Utils.formatRelativeTime(plugin.lastUpdated))])
        ]);

        const actions = Utils.createElement('div', {style: {display: 'flex', gap: '0.5rem', 'margin-top': '1rem'}}, [
            Components.button('Configure', {variant: 'secondary', size: 'sm', onClick: (e) => {e.stopPropagation(); this.configurePlugin(plugin);}}),
            Components.button('Evaluate', {variant: 'primary', size: 'sm', onClick: (e) => {e.stopPropagation(); this.evaluatePlugin(plugin);}})
        ]);

        card.appendChild(statusBadge);
        card.appendChild(header);
        card.appendChild(description);
        card.appendChild(tags);
        card.appendChild(stats);
        card.appendChild(actions);

        card.addEventListener('click', () => this.showPluginDetails(plugin));

        card.addEventListener('mouseenter', () => {
            card.style.borderColor = 'var(--primary)';
        });

        card.addEventListener('mouseleave', () => {
            card.style.borderColor = 'var(--border)';
        });

        return card;
    },

    createPluginListItem(plugin, index) {
        const item = Utils.createElement('div', {
            class: 'plugin-list-item card',
            style: {
                padding: '1.5rem',
                display: 'flex',
                'align-items': 'center',
                gap: '1.5rem',
                cursor: 'pointer',
                transition: 'all var(--duration-fast) var(--ease)',
                'animation-delay': `${index * 50}ms`
            }
        });

        const icon = this.createPluginIcon(plugin.type);

        const info = Utils.createElement('div', {style: {flex: '1', 'min-width': '0'}}, [
            Utils.createElement('div', {style: {display: 'flex', 'align-items': 'center', gap: '0.75rem', 'margin-bottom': '0.5rem'}}, [
                Utils.createElement('h3', {style: {'font-size': '1.125rem', 'font-weight': '600', color: 'var(--text-primary)'}}, [document.createTextNode(plugin.name)]),
                Components.badge(plugin.status, plugin.status === 'active' ? 'success' : 'warning'),
                Utils.createElement('span', {style: {'font-size': '0.75rem', color: 'var(--text-tertiary)'}}, [document.createTextNode(`v${plugin.version}`)])
            ]),
            Utils.createElement('p', {style: {'font-size': '0.875rem', color: 'var(--text-secondary)', 'margin-bottom': '0.5rem'}}, [document.createTextNode(plugin.description)]),
            Utils.createElement('div', {style: {display: 'flex', gap: '0.5rem', 'flex-wrap': 'wrap'}},
                plugin.inputTypes.map(type => Components.tag(type))
            )
        ]);

        const stats = Utils.createElement('div', {style: {display: 'flex', gap: '2rem', 'align-items': 'center'}}, [
            this.createStatColumn('Downloads', Utils.formatNumber(plugin.downloads)),
            this.createStatColumn('Rating', plugin.rating.toFixed(1) + ' ★'),
            this.createStatColumn('Updated', Utils.formatRelativeTime(plugin.lastUpdated))
        ]);

        const actions = Utils.createElement('div', {style: {display: 'flex', gap: '0.5rem'}}, [
            Components.button('Configure', {variant: 'secondary', size: 'sm', onClick: (e) => {e.stopPropagation(); this.configurePlugin(plugin);}}),
            Components.button('Evaluate', {variant: 'primary', size: 'sm', onClick: (e) => {e.stopPropagation(); this.evaluatePlugin(plugin);}})
        ]);

        item.appendChild(icon);
        item.appendChild(info);
        item.appendChild(stats);
        item.appendChild(actions);

        item.addEventListener('click', () => this.showPluginDetails(plugin));

        item.addEventListener('mouseenter', () => {
            item.style.transform = 'translateX(4px)';
            item.style.borderColor = 'var(--primary)';
        });

        item.addEventListener('mouseleave', () => {
            item.style.transform = 'translateX(0)';
            item.style.borderColor = 'var(--border)';
        });

        return item;
    },

    createPluginIcon(type) {
        const iconMap = {
            'visual': '<path d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"></path><path d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"></path>',
            'visual-inertial': '<path d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"></path>',
            'lidar': '<path d="M13 10V3L4 14h7v7l9-11h-7z"></path>',
            'lidar-inertial': '<path d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"></path>'
        };

        const icon = Utils.createElement('div', {
            style: {
                width: '3rem',
                height: '3rem',
                'border-radius': 'var(--radius-xl)',
                background: 'linear-gradient(135deg, var(--primary), var(--primary-light))',
                display: 'flex',
                'align-items': 'center',
                'justify-content': 'center',
                'flex-shrink': '0',
                transition: 'transform var(--duration-normal) var(--ease-spring)'
            }
        }, [
            Utils.createElement('svg', {style: {width: '1.5rem', height: '1.5rem', color: 'var(--text-inverse)'}, viewBox: '0 0 24 24', fill: 'none', stroke: 'currentColor', 'stroke-width': '2'}, []).innerHTML = iconMap[type] || iconMap['visual']
        ]);

        return icon;
    },

    createStat(icon, value) {
        return Utils.createElement('div', {style: {display: 'flex', 'align-items': 'center', gap: '0.25rem', 'font-size': '0.75rem', color: 'var(--text-secondary)'}}, [
            Utils.createElement('svg', {style: {width: '1rem', height: '1rem'}, viewBox: '0 0 24 24', fill: 'none', stroke: 'currentColor', 'stroke-width': '2'}, []).innerHTML = icon,
            document.createTextNode(value)
        ]);
    },

    createStatColumn(label, value) {
        return Utils.createElement('div', {style: {'text-align': 'center'}}, [
            Utils.createElement('div', {style: {'font-size': '0.875rem', 'font-weight': '600', color: 'var(--text-primary)', 'margin-bottom': '0.25rem'}}, [document.createTextNode(value)]),
            Utils.createElement('div', {style: {'font-size': '0.75rem', color: 'var(--text-tertiary)'}}, [document.createTextNode(label)])
        ]);
    },

    showPluginDetails(plugin) {
        const content = Utils.createElement('div', {}, [
            Utils.createElement('div', {style: {display: 'flex', 'align-items': 'center', gap: '1rem', 'margin-bottom': '1.5rem'}}, [
                this.createPluginIcon(plugin.type),
                Utils.createElement('div', {}, [
                    Utils.createElement('h3', {style: {'font-size': '1.25rem', 'font-weight': '600', 'margin-bottom': '0.25rem'}}, [document.createTextNode(plugin.name)]),
                    Utils.createElement('div', {style: {'font-size': '0.875rem', color: 'var(--text-secondary)'}}, [document.createTextNode(`by ${plugin.author} • v${plugin.version}`)])
                ])
            ]),
            Utils.createElement('p', {style: {'font-size': '0.875rem', color: 'var(--text-secondary)', 'line-height': '1.6', 'margin-bottom': '1.5rem'}}, [document.createTextNode(plugin.description)]),
            Utils.createElement('div', {style: {display: 'grid', 'grid-template-columns': 'repeat(2, 1fr)', gap: '1rem', 'margin-bottom': '1.5rem'}}, [
                this.createDetailItem('Type', plugin.type),
                this.createDetailItem('Status', plugin.status),
                this.createDetailItem('Downloads', Utils.formatNumber(plugin.downloads)),
                this.createDetailItem('Rating', plugin.rating.toFixed(1) + ' ★')
            ]),
            Utils.createElement('div', {style: {'margin-bottom': '1rem'}}, [
                Utils.createElement('div', {style: {'font-size': '0.75rem', 'font-weight': '600', 'text-transform': 'uppercase', 'letter-spacing': '0.05em', color: 'var(--text-tertiary)', 'margin-bottom': '0.5rem'}}, [document.createTextNode('Input Types')]),
                Utils.createElement('div', {style: {display: 'flex', gap: '0.5rem', 'flex-wrap': 'wrap'}},
                    plugin.inputTypes.map(type => Components.tag(type))
                )
            ])
        ]);

        Components.modal(plugin.name, content, {
            actions: [
                {label: 'Configure', variant: 'secondary', onClick: () => this.configurePlugin(plugin)},
                {label: 'Evaluate', variant: 'primary', onClick: () => this.evaluatePlugin(plugin)}
            ]
        });
    },

    createDetailItem(label, value) {
        return Utils.createElement('div', {}, [
            Utils.createElement('div', {style: {'font-size': '0.75rem', color: 'var(--text-tertiary)', 'margin-bottom': '0.25rem'}}, [document.createTextNode(label)]),
            Utils.createElement('div', {style: {'font-size': '0.875rem', 'font-weight': '600', color: 'var(--text-primary)'}}, [document.createTextNode(value)])
        ]);
    },

    configurePlugin(plugin) {
        Components.toast(`Opening configuration for ${plugin.name}`, 'info');
        // TODO: Open configuration modal
    },

    evaluatePlugin(plugin) {
        App.navigate('evaluate', {plugin: plugin.name});
    },

    showAddPluginModal() {
        const content = Utils.createElement('div', {}, [
            Utils.createElement('p', {style: {'font-size': '0.875rem', color: 'var(--text-secondary)', 'margin-bottom': '1.5rem'}}, [document.createTextNode('Add a new SLAM plugin to the framework')]),
            Components.input({label: 'Plugin Name', placeholder: 'my-slam-plugin'}),
            Components.input({label: 'Git Repository', placeholder: 'https://github.com/user/repo'}),
            Components.select({
                label: 'Plugin Type',
                options: [
                    {value: 'visual', label: 'Visual'},
                    {value: 'visual-inertial', label: 'Visual-Inertial'},
                    {value: 'lidar', label: 'LiDAR'},
                    {value: 'lidar-inertial', label: 'LiDAR-Inertial'}
                ]
            })
        ]);

        Components.modal('Add Plugin', content, {
            actions: [
                {label: 'Cancel', variant: 'secondary'},
                {label: 'Add Plugin', variant: 'primary', onClick: () => {
                    Components.toast('Plugin added successfully', 'success');
                }}
            ]
        });
    }
};
