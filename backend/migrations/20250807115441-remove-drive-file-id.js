module.exports = {
  up: async (queryInterface, Sequelize) => {
    await queryInterface.removeColumn("files", "drive_file_id");
  },

  down: async (queryInterface, Sequelize) => {
    await queryInterface.addColumn("files", "drive_file_id", {
      type: Sequelize.STRING,
      allowNull: false,
    });
  },
};
