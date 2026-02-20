module.exports = {
  devServer: {
    // 允许所有的主机头访问
    allowedHosts: 'all',
    // 如果你是旧版 Webpack（之前版本），可能需要下面这个：
    // disableHostCheck: true,
    
    // 保持你之前的代理配置
    proxy: {
      '/api': {
        target: 'http://localhost:6006',
        changeOrigin: true
      }
    }
  }
}