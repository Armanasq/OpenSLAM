const API = {
    baseURL: CONFIG.API_BASE_URL,
    headers: {'Content-Type': 'application/json'},
    requestInterceptors: [],
    responseInterceptors: [],

    addRequestInterceptor(interceptor) {
        this.requestInterceptors.push(interceptor);
    },

    addResponseInterceptor(interceptor) {
        this.responseInterceptors.push(interceptor);
    },

    async request(endpoint, options = {}) {
        let url = this.baseURL + endpoint;
        let config = {method: 'GET', headers: {...this.headers}, ...options};

        for (const interceptor of this.requestInterceptors) {
            const result = await interceptor(url, config);
            if (result) {url = result.url || url; config = result.config || config;}
        }

        try {
            const response = await fetch(url, config);
            let data = null;

            const contentType = response.headers.get('content-type');
            if (contentType && contentType.includes('application/json')) {
                data = await response.json();
            } else {
                data = await response.text();
            }

            let result = {ok: response.ok, status: response.status, data, response};

            for (const interceptor of this.responseInterceptors) {
                result = await interceptor(result) || result;
            }

            if (!response.ok) {
                const error = new Error(data.message || `HTTP ${response.status}`);
                error.status = response.status;
                error.data = data;
                throw error;
            }

            return result.data;
        } catch (error) {
            console.error('API Error:', error);
            throw error;
        }
    },

    get(endpoint, params = {}) {
        const query = Utils.buildQuery(params);
        const url = query ? `${endpoint}?${query}` : endpoint;
        return this.request(url, {method: 'GET'});
    },

    post(endpoint, data) {
        return this.request(endpoint, {method: 'POST', body: JSON.stringify(data)});
    },

    put(endpoint, data) {
        return this.request(endpoint, {method: 'PUT', body: JSON.stringify(data)});
    },

    patch(endpoint, data) {
        return this.request(endpoint, {method: 'PATCH', body: JSON.stringify(data)});
    },

    delete(endpoint) {
        return this.request(endpoint, {method: 'DELETE'});
    },

    upload(endpoint, file, onProgress) {
        return new Promise((resolve, reject) => {
            const formData = new FormData();
            formData.append('file', file);

            const xhr = new XMLHttpRequest();

            if (onProgress) {
                xhr.upload.addEventListener('progress', event => {
                    if (event.lengthComputable) {
                        const progress = (event.loaded / event.total) * 100;
                        onProgress(progress);
                    }
                });
            }

            xhr.addEventListener('load', () => {
                if (xhr.status >= 200 && xhr.status < 300) {
                    try {
                        const data = JSON.parse(xhr.responseText);
                        resolve(data);
                    } catch {
                        resolve(xhr.responseText);
                    }
                } else {
                    reject(new Error(`Upload failed: ${xhr.status}`));
                }
            });

            xhr.addEventListener('error', () => reject(new Error('Upload failed')));
            xhr.addEventListener('abort', () => reject(new Error('Upload aborted')));

            xhr.open('POST', this.baseURL + endpoint);
            xhr.send(formData);
        });
    },

    plugins: {
        list() {return API.get('/plugins');},
        get(name) {return API.get(`/plugins/${name}`);},
        evaluate(name, data) {return API.post(`/plugins/${name}/evaluate`, data);}
    },

    datasets: {
        list() {return API.get('/datasets');},
        get(id) {return API.get(`/datasets/${id}`);},
        upload(file, onProgress) {return API.upload('/datasets', file, onProgress);},
        delete(id) {return API.delete(`/datasets/${id}`);}
    },

    evaluations: {
        list(params) {return API.get('/evaluations', params);},
        get(id) {return API.get(`/evaluations/${id}`);},
        create(data) {return API.post('/evaluations', data);},
        delete(id) {return API.delete(`/evaluations/${id}`);}
    },

    results: {
        list(params) {return API.get('/evaluations', params);},
        get(id) {return API.get(`/evaluations/${id}`);},
        compare(ids) {return API.post('/compare', {ids});},
        export(id, format) {return API.get(`/evaluations/${id}/export/${format}`);}
    },

    batch: {
        create(data) {return API.post('/batch', data);},
        get(id) {return API.get(`/batch/${id}`);},
        list() {return API.get('/batch');},
        cancel(id) {return API.post(`/batch/${id}/cancel`);}
    },

    system: {
        status() {return API.get('/system/status');},
        settings() {return API.get('/system/settings');},
        updateSettings(data) {return API.put('/system/settings', data);}
    }
};

API.addRequestInterceptor((url, config) => {
    const token = localStorage.getItem('auth_token');
    if (token) {
        config.headers['Authorization'] = `Bearer ${token}`;
    }
    return {url, config};
});

API.addResponseInterceptor(result => {
    if (result.status === 401) {
        localStorage.removeItem('auth_token');
        window.location.href = '/login';
    }
    return result;
});

class WebSocketManager {
    constructor(url) {
        this.url = url;
        this.socket = null;
        this.isConnected = false;
    }

    connect() {
        return new Promise((resolve, reject) => {
            try {
                this.socket = io(this.url, {
                    transports: ['websocket', 'polling'],
                    reconnection: true,
                    reconnectionAttempts: 5,
                    reconnectionDelay: 1000
                });

                this.socket.on('connect', () => {
                    this.isConnected = true;
                    console.log('Socket.IO connected');
                    resolve();
                });

                this.socket.on('disconnect', () => {
                    this.isConnected = false;
                    console.log('Socket.IO disconnected');
                });

                this.socket.on('connect_error', (error) => {
                    console.error('Socket.IO connection error:', error);
                    reject(error);
                });

                this.socket.on('connected', (data) => {
                    console.log('Server message:', data.message);
                });

            } catch (error) {
                reject(error);
            }
        });
    }

    on(event, callback) {
        if (this.socket) {
            this.socket.on(event, callback);
        }
    }

    off(event, callback) {
        if (this.socket) {
            this.socket.off(event, callback);
        }
    }

    emit(event, data) {
        if (this.socket && this.isConnected) {
            this.socket.emit(event, data);
        }
    }

    disconnect() {
        if (this.socket) {
            this.socket.disconnect();
            this.socket = null;
            this.isConnected = false;
        }
    }
}

const WS = new WebSocketManager(CONFIG.WS_URL);
