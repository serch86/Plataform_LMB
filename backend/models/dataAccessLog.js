module.exports = (sequelize, DataTypes) => {
  return sequelize.define(
    "DataAccessLog",
    {
      // ID único para cada registro de log (UUID generado por la BD)
      id: {
        type: DataTypes.UUID,
        defaultValue: sequelize.literal("gen_random_uuid()"),
        primaryKey: true,
      },
      // Acción realizada
      action: { type: DataTypes.STRING, allowNull: false },
      // Fecha y hora
      timestamp: { type: DataTypes.DATE, defaultValue: DataTypes.NOW },
      // Datos adicionales y flexibles en formato JSON
      metadata: { type: DataTypes.JSONB },
    },
    {
      // Nombre real de la tabla en la base de datos
      tableName: "data_access_logs",
      // Desactiva los campos automáticos
      timestamps: false,
    }
  );
};
