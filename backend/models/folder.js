module.exports = (sequelize, DataTypes) => {
  return sequelize.define(
    "Folder",
    {
      id: {
        type: DataTypes.UUID,
        defaultValue: sequelize.literal("gen_random_uuid()"),
        primaryKey: true,
      },
      drive_folder_id: { type: DataTypes.STRING, allowNull: false },
      name: { type: DataTypes.STRING },
    },
    {
      tableName: "folders",
      timestamps: false,
    }
  );
};
