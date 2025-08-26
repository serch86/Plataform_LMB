require("dotenv").config();

// !!!!!!! VULNERABILIDAD DE SEGURIDAD !!!!!!!!
// quitar logs en produccion

console.log("GOOGLE_CLIENT_ID:", process.env.GOOGLE_CLIENT_ID);
console.log("GOOGLE_CLIENT_SECRET:", process.env.GOOGLE_CLIENT_SECRET);
console.log("GOOGLE_CALLBACK_URL:", process.env.GOOGLE_CALLBACK_URL);

const app = require("./app");
const db = require("./models");

const PORT = process.env.PORT || 3000;

db.sequelize
  .authenticate()
  .then(() => db.sequelize.sync()) // Considerar el uso de migraciones para producción en lugar de sync()
  .then(() => {
    app.listen(PORT, "0.0.0.0", () => {
      console.log(`Servidor corriendo en http://0.0.0.0:${PORT}`);
    });
  })
  .catch((err) => {
    console.error("Error al conectar o sincronizar la base de datos:", err);
    process.exit(1);
  });
