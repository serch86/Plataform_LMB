module.exports = (sequelize, DataTypes) => {
  return sequelize.define(
    "File",
    {
      id: {
        type: DataTypes.UUID,
        defaultValue: sequelize.literal("gen_random_uuid()"),
        primaryKey: true,
      },
      name: { type: DataTypes.STRING, allowNull: false },
      type: { type: DataTypes.STRING },
      uploaded_at: { type: DataTypes.DATE, defaultValue: DataTypes.NOW },
      bigquery_table: { type: DataTypes.STRING },
    },
    {
      tableName: "files",
      timestamps: false,
    }
  );
};
