module.exports = {
    async rewrites() {
      return [
        {
          source: '/api/:path*',
          destination: 'http://flask:8080/api/:path*',
        },
      ];
    },
  };
  