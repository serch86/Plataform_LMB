//const express = require("express");
//const routes = require("./routes");
//const passport = require("./config/passport");
//
//const app = express();
//app.use((req, res, next) => {
//  console.log(`[${new Date().toISOString()}] ${req.method} ${req.originalUrl}`);
//  next();
//});
//
//app.use(express.json());
//
//app.use(passport.initialize());
//
//app.get("/", (req, res) => {
//  res.send("Servidor backend funcionando");
//});
//
//app.use("/api", routes);
//
//module.exports = app;
//
const express = require("express");
const app = express();

app.get("/", (req, res) => {
  res.send("Servidor backend funcionando");
});

module.exports = app;
