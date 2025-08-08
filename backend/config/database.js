const { Sequelize } = require("sequelize");
require("dotenv").config();

const sequelize = new Sequelize(process.env.DATABASE_URL, {
  dialect: "postgres",
  logging: false, // Desactiva logs

  // pool de conexione
  // pool: {
  //   max: 100, // Máximo 5 conexiones activas
  //   min: 0, // Mínimo 0 conexiones
  //   acquire: 30000, // Tiempo máximo para obtener una conexión (ms)
  //   idle: 10000, // Tiempo de inactividad antes de liberar una conexión (ms)
  // },

  //Conexión por IP pública borra si la IP es privada
  /*
  dialectOptions: {
    ssl: {
      require: true,
      rejectUnauthorized: false, // necesario si el certificado no es verificado
    },
  },
  */
});

//borrar/comentar en produccion
sequelize
  .authenticate()
  .then(() => console.log("Conexión a la base de datos establecida."))
  .catch((err) => console.error("Error al conectar a la base de datos:", err));

module.exports = sequelize;
