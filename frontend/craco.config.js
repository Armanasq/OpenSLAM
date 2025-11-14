module.exports = {
  devServer: {
    port: 3001,
    allowedHosts: 'all',
    client: {
      overlay: {
        errors: true,
        warnings: false,
      },
    },
  },
  webpack: {
    configure: (webpackConfig) => {
      // Remove ESLint plugin to avoid errors during development
      webpackConfig.plugins = webpackConfig.plugins.filter(
        plugin => plugin && plugin.constructor && plugin.constructor.name !== 'ESLintWebpackPlugin'
      );
      return webpackConfig;
    }
  }
};