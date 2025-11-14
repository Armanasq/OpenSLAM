const Components = {
    toast(message, type = 'info', duration = CONFIG.TOAST.DURATION) {
        const container = document.getElementById('toastContainer');
        const toasts = container.querySelectorAll('.toast');

        if (toasts.length >= CONFIG.TOAST.MAX_TOASTS) {
            toasts[0].remove();
        }

        const icons = {
            success: '<path d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path>',
            error: '<path d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z"></path>',
            warning: '<path d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"></path>',
            info: '<path d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>'
        };

        const toast = Utils.createElement('div', {class: `toast ${type}`}, [
            Utils.createElement('div', {class: 'toast-header'}, [
                Utils.createElement('div', {class: 'toast-title'}, [
                    Utils.createElement('svg', {class: 'toast-icon', viewBox: '0 0 24 24', fill: 'none', stroke: 'currentColor', 'stroke-width': '2'}, []).innerHTML = icons[type],
                    document.createTextNode(type.charAt(0).toUpperCase() + type.slice(1))
                ]),
                Utils.createElement('button', {class: 'toast-close', onclick: () => this.removeToast(toast)}, [
                    Utils.createElement('svg', {viewBox: '0 0 24 24', fill: 'none', stroke: 'currentColor', 'stroke-width': '2'}, []).innerHTML = '<path d="M6 18L18 6M6 6l12 12"></path>'
                ])
            ]),
            Utils.createElement('div', {class: 'toast-body'}, [document.createTextNode(message)])
        ]);

        container.appendChild(toast);

        setTimeout(() => {
            toast.style.animation = 'toastSlideIn 300ms ease-out reverse';
            setTimeout(() => toast.remove(), 300);
        }, duration);

        return toast;
    },

    removeToast(toast) {
        toast.style.animation = 'toastSlideIn 300ms ease-out reverse';
        setTimeout(() => toast.remove(), 300);
    },

    modal(title, content, options = {}) {
        const {size = 'md', onClose, footer} = options;
        const backdrop = document.getElementById('modalBackdrop');

        const modal = Utils.createElement('div', {class: `modal active`}, [
            Utils.createElement('div', {class: `modal-content modal-${size}`}, [
                Utils.createElement('div', {class: 'modal-header'}, [
                    Utils.createElement('h3', {class: 'modal-title'}, [document.createTextNode(title)]),
                    Utils.createElement('button', {class: 'modal-close', onclick: () => this.closeModal(modal, backdrop, onClose)}, [
                        Utils.createElement('svg', {viewBox: '0 0 24 24', fill: 'none', stroke: 'currentColor', 'stroke-width': '2'}, []).innerHTML = '<path d="M6 18L18 6M6 6l12 12"></path>'
                    ])
                ]),
                Utils.createElement('div', {class: 'modal-body'}, [
                    typeof content === 'string' ? document.createTextNode(content) : content
                ]),
                footer ? Utils.createElement('div', {class: 'modal-footer'}, footer) : null
            ].filter(Boolean))
        ]);

        backdrop.classList.add('active');
        backdrop.onclick = () => this.closeModal(modal, backdrop, onClose);
        document.body.appendChild(modal);
        Utils.lockScroll();

        return modal;
    },

    closeModal(modal, backdrop, callback) {
        modal.classList.remove('active');
        backdrop.classList.remove('active');
        Utils.unlockScroll();
        setTimeout(() => modal.remove(), 300);
        if (callback) callback();
    },

    confirm(message, options = {}) {
        return new Promise(resolve => {
            const {title = 'Confirm', confirmText = 'Confirm', cancelText = 'Cancel'} = options;

            const footer = [
                Utils.createElement('button', {class: 'btn btn-secondary', onclick: () => {
                    this.closeModal(modal, backdrop);
                    resolve(false);
                }}, [document.createTextNode(cancelText)]),
                Utils.createElement('button', {class: 'btn btn-primary', onclick: () => {
                    this.closeModal(modal, backdrop);
                    resolve(true);
                }}, [document.createTextNode(confirmText)])
            ];

            const backdrop = document.getElementById('modalBackdrop');
            const modal = this.modal(title, message, {footer, onClose: () => resolve(false)});
        });
    },

    dropdown(trigger, items) {
        const dropdown = Utils.createElement('div', {class: 'dropdown'});
        const menu = Utils.createElement('div', {class: 'dropdown-menu'},
            items.map(item => {
                if (item === 'divider') {
                    return Utils.createElement('div', {class: 'dropdown-divider'});
                }
                return Utils.createElement('a', {
                    class: 'dropdown-item',
                    onclick: () => {
                        item.action();
                        dropdown.classList.remove('active');
                    }
                }, [
                    item.icon ? Utils.createElement('svg', {viewBox: '0 0 24 24', fill: 'none', stroke: 'currentColor', 'stroke-width': '2'}, []).innerHTML = item.icon : null,
                    document.createTextNode(item.label)
                ].filter(Boolean));
            })
        );

        trigger.addEventListener('click', e => {
            e.stopPropagation();
            dropdown.classList.toggle('active');
        });

        document.addEventListener('click', () => dropdown.classList.remove('active'));

        dropdown.appendChild(menu);
        trigger.parentNode.insertBefore(dropdown, trigger.nextSibling);
        dropdown.insertBefore(trigger, dropdown.firstChild);

        return dropdown;
    },

    card(options = {}) {
        const {title, subtitle, body, footer, headerActions} = options;

        const card = Utils.createElement('div', {class: 'card'});

        if (title) {
            const header = Utils.createElement('div', {class: 'card-header'}, [
                Utils.createElement('div', {}, [
                    Utils.createElement('h3', {class: 'card-title'}, [document.createTextNode(title)]),
                    subtitle ? Utils.createElement('p', {class: 'card-subtitle'}, [document.createTextNode(subtitle)]) : null
                ].filter(Boolean)),
                headerActions ? Utils.createElement('div', {class: 'card-actions'}, headerActions) : null
            ].filter(Boolean));
            card.appendChild(header);
        }

        if (body) {
            const bodyEl = Utils.createElement('div', {class: 'card-body'});
            if (typeof body === 'string') {
                bodyEl.textContent = body;
            } else {
                bodyEl.appendChild(body);
            }
            card.appendChild(bodyEl);
        }

        if (footer) {
            const footerEl = Utils.createElement('div', {class: 'card-footer'}, Array.isArray(footer) ? footer : [footer]);
            card.appendChild(footerEl);
        }

        return card;
    },

    button(text, options = {}) {
        const {variant = 'primary', size, icon, loading, disabled, onclick} = options;

        const classes = ['btn', `btn-${variant}`];
        if (size) classes.push(`btn-${size}`);
        if (loading) classes.push('loading');

        const children = [];
        if (loading) {
            children.push(Utils.createElement('span', {class: 'loading-spinner'}));
        }
        if (icon) {
            const svg = Utils.createElement('svg', {viewBox: '0 0 24 24', fill: 'none', stroke: 'currentColor', 'stroke-width': '2'});
            svg.innerHTML = icon;
            children.push(svg);
        }
        children.push(document.createTextNode(text));

        return Utils.createElement('button', {class: classes.join(' '), disabled, onclick}, children);
    },

    input(options = {}) {
        const {label, type = 'text', placeholder, value, required, error, help, icon, onchange} = options;

        const group = Utils.createElement('div', {class: 'input-group'});

        if (label) {
            const labelEl = Utils.createElement('label', {class: required ? 'input-label required' : 'input-label'}, [document.createTextNode(label)]);
            group.appendChild(labelEl);
        }

        const wrapper = Utils.createElement('div', {class: 'input-wrapper'});

        const input = Utils.createElement('input', {
            class: `input ${icon ? 'input-with-icon' : ''} ${error ? 'error' : ''}`,
            type,
            placeholder,
            value: value || '',
            onchange
        });
        wrapper.appendChild(input);

        if (icon) {
            const iconEl = Utils.createElement('svg', {class: 'input-icon', viewBox: '0 0 24 24', fill: 'none', stroke: 'currentColor', 'stroke-width': '2'});
            iconEl.innerHTML = icon;
            wrapper.appendChild(iconEl);
        }

        group.appendChild(wrapper);

        if (error) {
            group.appendChild(Utils.createElement('span', {class: 'input-error'}, [document.createTextNode(error)]));
        } else if (help) {
            group.appendChild(Utils.createElement('span', {class: 'input-help'}, [document.createTextNode(help)]));
        }

        return group;
    },

    select(options = {}) {
        const {label, choices, value, required, onchange} = options;

        const group = Utils.createElement('div', {class: 'input-group'});

        if (label) {
            const labelEl = Utils.createElement('label', {class: required ? 'input-label required' : 'input-label'}, [document.createTextNode(label)]);
            group.appendChild(labelEl);
        }

        const select = Utils.createElement('select', {class: 'input select', onchange});

        choices.forEach(choice => {
            const option = Utils.createElement('option', {value: choice.value}, [document.createTextNode(choice.label)]);
            if (choice.value === value) option.selected = true;
            select.appendChild(option);
        });

        group.appendChild(select);

        return group;
    },

    checkbox(options = {}) {
        const {label, checked, onchange} = options;

        const wrapper = Utils.createElement('label', {class: 'checkbox-wrapper'});

        const input = Utils.createElement('input', {type: 'checkbox', class: 'checkbox-input', checked, onchange});
        const box = Utils.createElement('span', {class: 'checkbox'});
        const labelEl = Utils.createElement('span', {class: 'checkbox-label'}, [document.createTextNode(label)]);

        wrapper.appendChild(input);
        wrapper.appendChild(box);
        wrapper.appendChild(labelEl);

        return wrapper;
    },

    switch(options = {}) {
        const {label, checked, onchange} = options;

        const wrapper = Utils.createElement('label', {class: 'switch-wrapper'});

        const input = Utils.createElement('input', {type: 'checkbox', class: 'switch-input', checked, onchange});
        const switchEl = Utils.createElement('span', {class: 'switch'});
        const labelEl = Utils.createElement('span', {class: 'switch-label'}, [document.createTextNode(label)]);

        wrapper.appendChild(input);
        wrapper.appendChild(switchEl);
        wrapper.appendChild(labelEl);

        return wrapper;
    },

    badge(text, variant = 'primary', withDot = false) {
        const classes = ['badge', `badge-${variant}`];
        if (withDot) classes.push('badge-dot');
        return Utils.createElement('span', {class: classes.join(' ')}, [document.createTextNode(text)]);
    },

    tag(text, onRemove) {
        const tag = Utils.createElement('span', {class: 'tag'}, [
            document.createTextNode(text),
            onRemove ? Utils.createElement('button', {class: 'tag-close', onclick: () => onRemove(tag)}, [
                Utils.createElement('svg', {viewBox: '0 0 24 24', fill: 'none', stroke: 'currentColor', 'stroke-width': '2'}, []).innerHTML = '<path d="M6 18L18 6M6 6l12 12"></path>'
            ]) : null
        ].filter(Boolean));
        return tag;
    },

    progress(value, max = 100) {
        const percent = (value / max) * 100;
        const bar = Utils.createElement('div', {class: 'progress-bar', style: {width: percent + '%'}});
        return Utils.createElement('div', {class: 'progress'}, [bar]);
    },

    spinner(size = 'md') {
        return Utils.createElement('div', {class: `spinner spinner-${size}`});
    },

    skeleton(type = 'text') {
        return Utils.createElement('div', {class: `skeleton skeleton-${type}`});
    },

    tabs(items, activeIndex = 0) {
        const tabsEl = Utils.createElement('div', {class: 'tabs'});
        const contents = [];

        items.forEach((item, index) => {
            const tab = Utils.createElement('button', {
                class: index === activeIndex ? 'tab active' : 'tab',
                onclick: () => this.switchTab(tabsEl, contents, index)
            }, [document.createTextNode(item.label)]);
            tabsEl.appendChild(tab);

            const content = Utils.createElement('div', {
                class: index === activeIndex ? 'tab-content active' : 'tab-content'
            });
            if (typeof item.content === 'string') {
                content.textContent = item.content;
            } else {
                content.appendChild(item.content);
            }
            contents.push(content);
        });

        return {tabs: tabsEl, contents};
    },

    switchTab(tabsEl, contents, index) {
        tabsEl.querySelectorAll('.tab').forEach((tab, i) => {
            tab.classList.toggle('active', i === index);
        });
        contents.forEach((content, i) => {
            content.classList.toggle('active', i === index);
        });
    },

    table(columns, data, options = {}) {
        const {sortable = true, onRowClick} = options;

        const wrapper = Utils.createElement('div', {class: 'table-wrapper'});
        const table = Utils.createElement('table', {class: 'table'});

        const thead = Utils.createElement('thead');
        const headerRow = Utils.createElement('tr');

        columns.forEach((col, index) => {
            const th = Utils.createElement('th', {
                onclick: sortable ? () => this.sortTable(data, col.key, table) : null
            }, [document.createTextNode(col.label)]);
            headerRow.appendChild(th);
        });
        thead.appendChild(headerRow);
        table.appendChild(thead);

        const tbody = Utils.createElement('tbody');
        this.renderTableRows(tbody, columns, data, onRowClick);
        table.appendChild(tbody);

        wrapper.appendChild(table);

        return wrapper;
    },

    renderTableRows(tbody, columns, data, onRowClick) {
        tbody.innerHTML = '';
        data.forEach(row => {
            const tr = Utils.createElement('tr', {
                onclick: onRowClick ? () => onRowClick(row) : null
            });

            columns.forEach(col => {
                const value = row[col.key];
                const td = Utils.createElement('td');

                if (col.render) {
                    const rendered = col.render(value, row);
                    if (typeof rendered === 'string') {
                        td.textContent = rendered;
                    } else {
                        td.appendChild(rendered);
                    }
                } else {
                    td.textContent = value;
                }

                tr.appendChild(td);
            });

            tbody.appendChild(tr);
        });
    },

    sortTable(data, key, table) {
        const isAscending = table.dataset.sortKey === key && table.dataset.sortDir === 'asc';
        const sorted = Utils.sortBy(data, key, !isAscending);
        table.dataset.sortKey = key;
        table.dataset.sortDir = isAscending ? 'desc' : 'asc';
        const tbody = table.querySelector('tbody');
        const columns = Array.from(table.querySelectorAll('th')).map(th => ({label: th.textContent, key}));
        this.renderTableRows(tbody, columns, sorted);
    },

    emptyState(options = {}) {
        const {icon, title, description, action} = options;

        const state = Utils.createElement('div', {class: 'empty-state'}, [
            icon ? Utils.createElement('svg', {class: 'empty-state-icon', viewBox: '0 0 24 24', fill: 'none', stroke: 'currentColor', 'stroke-width': '2'}, []).innerHTML = icon : null,
            title ? Utils.createElement('h3', {class: 'empty-state-title'}, [document.createTextNode(title)]) : null,
            description ? Utils.createElement('p', {class: 'empty-state-description'}, [document.createTextNode(description)]) : null,
            action
        ].filter(Boolean));

        return state;
    },

    fileUpload(options = {}) {
        const {accept, maxSize = CONFIG.FILE.MAX_SIZE, onSelect, multiple = false} = options;

        const input = Utils.createElement('input', {
            type: 'file',
            accept: accept || CONFIG.FILE.ALLOWED_TYPES.join(','),
            multiple,
            style: {display: 'none'},
            onchange: async (e) => {
                const files = Array.from(e.target.files);

                for (const file of files) {
                    if (!Utils.validateFileSize(file.size, maxSize)) {
                        Components.toast(`File ${file.name} exceeds maximum size of ${Utils.formatBytes(maxSize)}`, 'error');
                        continue;
                    }

                    if (accept && !Utils.validateFileType(file.name, accept.split(','))) {
                        Components.toast(`File ${file.name} has invalid type`, 'error');
                        continue;
                    }

                    if (onSelect) await onSelect(file);
                }

                input.value = '';
            }
        });

        const button = Utils.createElement('button', {
            class: 'btn btn-secondary',
            onclick: () => input.click()
        }, [
            Utils.createElement('svg', {viewBox: '0 0 24 24', fill: 'none', stroke: 'currentColor', 'stroke-width': '2'}, []).innerHTML = '<path d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"></path>',
            document.createTextNode('Upload File')
        ]);

        const container = Utils.createElement('div', {class: 'file-upload'});
        container.appendChild(input);
        container.appendChild(button);

        return container;
    },

    pagination(totalItems, pageSize, currentPage, onChange) {
        const totalPages = Math.ceil(totalItems / pageSize);

        const container = Utils.createElement('div', {class: 'pagination'});

        const prevBtn = Utils.createElement('button', {
            class: 'btn btn-icon btn-secondary',
            disabled: currentPage === 1,
            onclick: () => onChange(currentPage - 1)
        }, [
            Utils.createElement('svg', {viewBox: '0 0 24 24', fill: 'none', stroke: 'currentColor', 'stroke-width': '2'}, []).innerHTML = '<path d="M15 19l-7-7 7-7"></path>'
        ]);
        container.appendChild(prevBtn);

        const info = Utils.createElement('span', {class: 'pagination-info'}, [
            document.createTextNode(`Page ${currentPage} of ${totalPages}`)
        ]);
        container.appendChild(info);

        const nextBtn = Utils.createElement('button', {
            class: 'btn btn-icon btn-secondary',
            disabled: currentPage === totalPages,
            onclick: () => onChange(currentPage + 1)
        }, [
            Utils.createElement('svg', {viewBox: '0 0 24 24', fill: 'none', stroke: 'currentColor', 'stroke-width': '2'}, []).innerHTML = '<path d="M9 5l7 7-7 7"></path>'
        ]);
        container.appendChild(nextBtn);

        return container;
    }
};
