module.exports = (sequelize, DataTypes) => {
  return sequelize.define(
    "User",
    {
      id: {
        type: DataTypes.UUID,
        defaultValue: sequelize.literal("gen_random_uuid()"),
        primaryKey: true,
      },
      email: { type: DataTypes.STRING, unique: true, allowNull: false },
      password_hash: { type: DataTypes.TEXT },
      google_id: { type: DataTypes.STRING },
      role: { type: DataTypes.STRING, defaultValue: "viewer" },
      language: { type: DataTypes.STRING, defaultValue: "en" },
      created_at: { type: DataTypes.DATE, defaultValue: DataTypes.NOW },
    },
    {
      tableName: "users",
      timestamps: false,
    }
  );
};
