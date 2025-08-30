const path = require('path');

module.exports = function override(config, env) {
  // Add alias for easier imports
  config.resolve.alias = {
    ...config.resolve.alias,
    '@': path.resolve(__dirname, 'src'),
  };

  return config;
};

module.exports.devServer = function(configFunction) {
  return function(proxy, allowedHost) {
    const config = configFunction(proxy, allowedHost);

    // Fix allowedHosts issue
    if (config.allowedHosts && Array.isArray(config.allowedHosts)) {
      config.allowedHosts = config.allowedHosts.filter(host => host && typeof host === 'string' && host.length > 0);
      if (config.allowedHosts.length === 0) {
        config.allowedHosts = 'all';
      }
    }

    return config;
  };
};
