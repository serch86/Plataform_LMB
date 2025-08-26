const express = require("express");
const routes = require("./routes");
const passport = require("./config/passport");
const logger = require("./config/logger"); // Logger centralizado

const app = express();

app.use((req, res, next) => {
  logger.info(`${req.method} ${req.originalUrl}`);
  next();
});

app.use(express.json());

app.use((req, res, next) => {
  logger.info("Inicializando Passport");
  next();
});
app.use(passport.initialize());

app.use((req, res, next) => {
  if (req.originalUrl.startsWith("/api")) {
    logger.info("Montando rutas en /api");
  }
  next();
});
app.use("/api", routes);

app.get("/", (req, res) => {
  logger.info("Ruta / llamada");
  res.send("Servidor backend funcionando");
});

module.exports = app;
