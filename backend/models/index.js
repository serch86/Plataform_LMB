const { Sequelize } = require("sequelize");

const sequelize = new Sequelize(
  process.env.DB_NAME || "baseball_platform",
  process.env.DB_USER || "postgres",
  process.env.DB_PASS || "admin123",
  {
    host: process.env.DB_HOST || "localhost",
    dialect: "postgres",
    logging: false,
  }
);

const db = {};

db.Sequelize = Sequelize;
db.sequelize = sequelize;

db.User = require("./user")(sequelize, Sequelize);
db.File = require("./file")(sequelize, Sequelize);
db.DataAccessLog = require("./dataAccessLog")(sequelize, Sequelize);
db.Folder = require("./folder")(sequelize, Sequelize);

// User ↔ File
db.User.hasMany(db.File, { foreignKey: "owner_id" });
db.File.belongsTo(db.User, { foreignKey: "owner_id" });

// User ↔ DataAccessLog
db.User.hasMany(db.DataAccessLog, { foreignKey: "user_id" });
db.DataAccessLog.belongsTo(db.User, { foreignKey: "user_id" });

// File ↔ DataAccessLog
db.File.hasMany(db.DataAccessLog, { foreignKey: "file_id" });
db.DataAccessLog.belongsTo(db.File, { foreignKey: "file_id" });

// User ↔ Folder
db.User.hasMany(db.Folder, { foreignKey: "owner_id" });
db.Folder.belongsTo(db.User, { foreignKey: "owner_id" });

module.exports = db;
