const App = {
    currentView: 'dashboard',
    currentParams: {},
    views: {
        dashboard: DashboardView,
        plugins: PluginsView,
        datasets: DatasetsView,
        evaluate: EvaluateView,
        results: ResultsView,
        compare: CompareView,
        batch: BatchView,
        settings: SettingsView
    },

    async init() {
        this.setupNavigation();
        this.setupTheme();
        this.setupEventListeners();
        await this.connectWebSocket();

        const hash = window.location.hash.slice(1) || 'dashboard';
        this.navigate(hash);

        this.showWelcomeMessage();
    },

    setupNavigation() {
        const navItems = document.querySelectorAll('.nav-item');
        navItems.forEach(item => {
            item.addEventListener('click', (e) => {
                e.preventDefault();
                const view = item.getAttribute('data-view');
                if (view) {
                    this.navigate(view);
                }
            });
        });

        window.addEventListener('hashchange', () => {
            const hash = window.location.hash.slice(1) || 'dashboard';
            const [view, params] = hash.split('?');
            this.navigate(view, this.parseParams(params));
        });
    },

    setupTheme() {
        const themeToggle = document.getElementById('theme-toggle');
        if (themeToggle) {
            themeToggle.addEventListener('click', () => {
                this.toggleTheme();
            });
        }

        const sidebarToggle = document.querySelector('.sidebar-toggle');
        if (sidebarToggle) {
            sidebarToggle.addEventListener('click', () => {
                this.toggleSidebar();
            });
        }
    },

    setupEventListeners() {
        document.addEventListener('click', (e) => {
            const dropdowns = document.querySelectorAll('.dropdown.active');
            dropdowns.forEach(dropdown => {
                if (!dropdown.contains(e.target)) {
                    dropdown.classList.remove('active');
                }
            });
        });

        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                const modal = document.querySelector('.modal-backdrop.active');
                if (modal) {
                    modal.classList.remove('active');
                    const modalContent = document.querySelector('.modal');
                    if (modalContent) modalContent.remove();
                }
            }

            if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
                e.preventDefault();
                this.showCommandPalette();
            }
        });

        window.addEventListener('beforeunload', (e) => {
            if (this.hasUnsavedChanges()) {
                e.preventDefault();
                e.returnValue = '';
            }
        });
    },

    async connectWebSocket() {
        try {
            await WS.connect();
            console.log('WebSocket connected');

            WS.on('connect', () => {
                Components.toast('Connected to server', 'success');
            });

            WS.on('disconnect', () => {
                Components.toast('Disconnected from server', 'warning');
            });

            WS.on('error', (error) => {
                console.error('WebSocket error:', error);
                Components.toast('Connection error', 'error');
            });
        } catch (error) {
            console.error('Failed to connect WebSocket:', error);
        }
    },

    async navigate(view, params = {}) {
        if (!this.views[view]) {
            console.error(`View "${view}" not found`);
            view = 'dashboard';
        }

        this.currentView = view;
        this.currentParams = params;

        this.updateActiveNav(view);
        this.updatePageTitle(view);
        this.hideAllViews();
        this.showView(view);

        window.location.hash = view + (Object.keys(params).length > 0 ? '?' + new URLSearchParams(params).toString() : '');

        const viewInstance = this.views[view];
        if (viewInstance && typeof viewInstance.render === 'function') {
            await viewInstance.render(params);
        }

        this.scrollToTop();
    },

    updateActiveNav(view) {
        const navItems = document.querySelectorAll('.nav-item');
        navItems.forEach(item => {
            const itemView = item.getAttribute('data-view');
            if (itemView === view) {
                item.classList.add('active');
            } else {
                item.classList.remove('active');
            }
        });
    },

    updatePageTitle(view) {
        const titles = {
            dashboard: 'Dashboard',
            plugins: 'Plugins',
            datasets: 'Datasets',
            evaluate: 'Evaluate',
            results: 'Results',
            compare: 'Compare',
            batch: 'Batch Evaluations',
            settings: 'Settings'
        };

        document.title = `${titles[view] || 'OpenSLAM'} - OpenSLAM`;

        const pageTitle = document.querySelector('.page-title');
        if (pageTitle) {
            pageTitle.textContent = titles[view] || 'OpenSLAM';
        }
    },

    hideAllViews() {
        const views = document.querySelectorAll('.view');
        views.forEach(view => {
            view.classList.remove('active');
        });
    },

    showView(view) {
        const viewElement = document.getElementById(`view-${view}`);
        if (viewElement) {
            viewElement.classList.add('active');
        }
    },

    parseParams(paramsString) {
        if (!paramsString) return {};
        const params = {};
        const urlParams = new URLSearchParams(paramsString);
        for (const [key, value] of urlParams) {
            params[key] = value;
        }
        return params;
    },

    scrollToTop() {
        const contentArea = document.querySelector('.content-area');
        if (contentArea) {
            Utils.smoothScrollTo(contentArea);
        }
    },

    toggleTheme() {
        const root = document.documentElement;
        const currentTheme = root.getAttribute('data-theme') || 'light';
        const newTheme = currentTheme === 'light' ? 'dark' : 'light';

        root.setAttribute('data-theme', newTheme);
        localStorage.setItem('theme', newTheme);

        const themeIconLight = document.querySelector('.theme-icon-light');
        const themeIconDark = document.querySelector('.theme-icon-dark');

        if (newTheme === 'dark') {
            if (themeIconLight) themeIconLight.style.display = 'none';
            if (themeIconDark) themeIconDark.style.display = 'block';
        } else {
            if (themeIconLight) themeIconLight.style.display = 'block';
            if (themeIconDark) themeIconDark.style.display = 'none';
        }

        Components.toast(`Switched to ${newTheme} theme`, 'info');
    },

    toggleSidebar() {
        const sidebar = document.querySelector('.sidebar');
        if (sidebar) {
            sidebar.classList.toggle('collapsed');
            localStorage.setItem('sidebar-collapsed', sidebar.classList.contains('collapsed'));
        }
    },

    showCommandPalette() {
        const commands = [
            {label: 'Go to Dashboard', action: () => this.navigate('dashboard'), icon: '<path d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6"></path>'},
            {label: 'Browse Plugins', action: () => this.navigate('plugins'), icon: '<path d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4"></path>'},
            {label: 'Upload Dataset', action: () => this.navigate('datasets'), icon: '<path d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"></path>'},
            {label: 'Run Evaluation', action: () => this.navigate('evaluate'), icon: '<path d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z"></path>'},
            {label: 'View Results', action: () => this.navigate('results'), icon: '<path d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"></path>'},
            {label: 'Compare Results', action: () => this.navigate('compare'), icon: '<path d="M9 17V7m0 10a2 2 0 01-2 2H5a2 2 0 01-2-2V7a2 2 0 012-2h2a2 2 0 012 2m0 10a2 2 0 002 2h2a2 2 0 002-2M9 7a2 2 0 012-2h2a2 2 0 012 2m0 10V7m0 10a2 2 0 002 2h2a2 2 0 002-2V7a2 2 0 00-2-2h-2a2 2 0 00-2 2"></path>'},
            {label: 'Settings', action: () => this.navigate('settings'), icon: '<path d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"></path><path d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"></path>'}
        ];

        const searchInput = Components.input({
            placeholder: 'Search commands...',
            style: {'margin-bottom': '1rem'}
        });

        const commandList = Utils.createElement('div', {style: {display: 'flex', 'flex-direction': 'column', gap: '0.5rem', 'max-height': '400px', 'overflow-y': 'auto'}},
            commands.map(command => {
                const item = Utils.createElement('button', {
                    class: 'card',
                    style: {
                        padding: '1rem',
                        display: 'flex',
                        'align-items': 'center',
                        gap: '1rem',
                        border: '1px solid var(--border)',
                        background: 'var(--bg-primary)',
                        cursor: 'pointer',
                        'text-align': 'left',
                        transition: 'all var(--duration-fast) var(--ease)'
                    },
                    onclick: () => {
                        command.action();
                        const modal = document.querySelector('.modal-backdrop');
                        if (modal) modal.click();
                    }
                }, [
                    Utils.createElement('svg', {style: {width: '1.25rem', height: '1.25rem', color: 'var(--primary)', 'flex-shrink': '0'}, viewBox: '0 0 24 24', fill: 'none', stroke: 'currentColor', 'stroke-width': '2'}, []).innerHTML = command.icon,
                    Utils.createElement('span', {style: {'font-size': '0.875rem', 'font-weight': '500'}}, [document.createTextNode(command.label)])
                ]);

                item.addEventListener('mouseenter', () => {
                    item.style.background = 'var(--bg-secondary)';
                    item.style.transform = 'translateX(4px)';
                });

                item.addEventListener('mouseleave', () => {
                    item.style.background = 'var(--bg-primary)';
                    item.style.transform = 'translateX(0)';
                });

                return item;
            })
        );

        const content = Utils.createElement('div', {}, [searchInput, commandList]);

        Components.modal('Command Palette', content, {
            actions: []
        });

        setTimeout(() => {
            searchInput.focus();
        }, 100);
    },

    showWelcomeMessage() {
        const hasSeenWelcome = localStorage.getItem('hasSeenWelcome');
        if (!hasSeenWelcome) {
            setTimeout(() => {
                Components.toast('Welcome to OpenSLAM! 👋', 'success', 3000);
                localStorage.setItem('hasSeenWelcome', 'true');
            }, 1000);
        }
    },

    hasUnsavedChanges() {
        return false;
    },

    getSystemStatus() {
        return {
            online: navigator.onLine,
            lastSync: new Date(),
            version: '1.0.0'
        };
    }
};

document.addEventListener('DOMContentLoaded', () => {
    App.init();
});

window.addEventListener('online', () => {
    Components.toast('Back online', 'success');
});

window.addEventListener('offline', () => {
    Components.toast('You are offline', 'warning');
});

window.onerror = function(msg, url, lineNo, columnNo, error) {
    console.error('Error: ' + msg + '\nURL: ' + url + '\nLine: ' + lineNo + '\nColumn: ' + columnNo + '\nError object: ' + JSON.stringify(error));
    Components.toast('An error occurred. Please try again.', 'error');
    return false;
};
