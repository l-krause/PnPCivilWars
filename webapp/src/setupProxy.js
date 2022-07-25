const { createProxyMiddleware } = require('http-proxy-middleware');

module.exports = function (app) {
    app.use(
        createProxyMiddleware("/socket.io",{
            target: 'https://dnd.romanh.de/',
            changeOrigin: true,
            ws: true
        })
    );
}