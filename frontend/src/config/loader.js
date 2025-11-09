class Config {
  constructor() {
    this.data = null
    this.callbacks = []
  }
  async load() {
    const response = await fetch('/api/config')
    if (!response.ok) {
      return {error: 'Failed to load config', code: 1004, details: {status: response.status}, recovery: 'Check config file syntax'}
    }
    this.data = await response.json()
    return {status: 'ok'}
  }
  get(path) {
    if (!this.data || !this.data.data) {
      return null
    }
    const parts = path.split('.')
    let current = this.data.data
    for (const part of parts) {
      if (current && typeof current === 'object' && part in current) {
        current = current[part]
      } else {
        return null
      }
    }
    return current
  }
  subscribe(callback) {
    this.callbacks.push(callback)
  }
  notify(newData) {
    this.data = newData
    this.callbacks.forEach(cb => cb(this.data))
  }
}
export default Config
