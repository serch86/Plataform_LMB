module.exports = (sequelize, DataTypes) => {
  return sequelize.define(
    "DataAccessLog",
    {
      id: {
        type: DataTypes.UUID,
        defaultValue: sequelize.literal("gen_random_uuid()"),
        primaryKey: true,
      },
      action: { type: DataTypes.STRING, allowNull: false },
      timestamp: { type: DataTypes.DATE, defaultValue: DataTypes.NOW },
      metadata: { type: DataTypes.JSONB },
    },
    {
      tableName: "data_access_logs",
      timestamps: false,
    }
  );
};
