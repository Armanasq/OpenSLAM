class ConfigSync {
  constructor(config) {
    this.config = config
    this.ws = null
  }
  connect() {
    const wsUrl = this.config.get('urls.websocket_url')
    if (!wsUrl) {
      return {error: 'WebSocket URL not configured', code: 1004, details: {}, recovery: 'Check config file syntax'}
    }
    this.ws = new WebSocket(wsUrl)
    this.ws.onmessage = (event) => {
      const msg = JSON.parse(event.data)
      if (msg.type === 'config_update') {
        this.config.notify(msg.payload)
      }
    }
    this.ws.onerror = (error) => {
      console.error('WebSocket error:', error)
    }
    return {status: 'ok'}
  }
  disconnect() {
    if (this.ws) {
      this.ws.close()
      this.ws = null
    }
    return {status: 'ok'}
  }
}
export default ConfigSync
