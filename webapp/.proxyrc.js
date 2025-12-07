const path = require("path");
const serveStatic = require("serve-static");

const assetsPath = path.join(__dirname, "public", "img");
const pathToServe = "/img";

module.exports = function (app) {
  app.use(pathToServe, serveStatic(assetsPath));
};