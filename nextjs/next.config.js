module.exports = {
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'http://flask:8080/api/:path*',
      },
    ];
  },
  // Enable webpack polling for hot reloading in Docker
  webpack: (config) => {
    config.watchOptions = {
      poll: 1000, // Check for changes every second
      aggregateTimeout: 300, // Delay before rebuilding
    };
    return config;
  },
};
  