const db = require("./models");

(async () => {
  try {
    await db.sequelize.authenticate();
    console.log("Conexión a la base de datos exitosa.");

    // Producción
    // Crea las tablas si no existen.
    // await db.sequelize.sync();

    // Desarrollo continuo
    // agrega/ajusta columnas
    await db.sequelize.sync({ alter: true });

    // Limpieza total/pruebas controladas
    // Elimina todas las tablas y las recrea desde cero según los modelos
    // await db.sequelize.sync({ force: true });

    console.log("Modelos sincronizados con éxito.");
    process.exit(0);
  } catch (error) {
    console.error("Error al sincronizar modelos:", error);
    process.exit(1);
  }
})();
