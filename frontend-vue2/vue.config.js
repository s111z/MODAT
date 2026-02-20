const { defineConfig } = require('@vue/cli-service')

module.exports = defineConfig({
  transpileDependencies: true,
  devServer: {
    // 关键配置：允许所有外部访问
    historyApiFallback: true,
    allowedHosts: "all", 
    // 下面这个是给旧版 Webpack 备用的，新版加了也没坏处
    client: {
      overlay: false,
    },
    // 你的代理配置
    proxy: {
      '/api': {
        target: 'http://localhost:6006',
        changeOrigin: true,
        pathRewrite: { '^/api': '' }
      }
    }
  }
})