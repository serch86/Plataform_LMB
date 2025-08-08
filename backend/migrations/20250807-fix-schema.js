"use strict";

module.exports = {
  up: async (queryInterface, Sequelize) => {
    // Eliminar columna 'name' de 'users' si existe
    const tableUsers = await queryInterface.describeTable("users");
    if (tableUsers.name) {
      await queryInterface.removeColumn("users", "name");
    }

    // Cambiar owner_id a NOT NULL en 'files' si es nullable
    const tableFiles = await queryInterface.describeTable("files");
    if (tableFiles.owner_id && tableFiles.owner_id.allowNull === true) {
      await queryInterface.changeColumn("files", "owner_id", {
        type: Sequelize.UUID,
        allowNull: false,
        references: {
          model: "users",
          key: "id",
        },
        onDelete: "CASCADE",
      });
    }

    // Cambiar owner_id a NOT NULL en 'folders' si es nullable
    const tableFolders = await queryInterface.describeTable("folders");
    if (tableFolders.owner_id && tableFolders.owner_id.allowNull === true) {
      await queryInterface.changeColumn("folders", "owner_id", {
        type: Sequelize.UUID,
        allowNull: false,
        references: {
          model: "users",
          key: "id",
        },
        onDelete: "CASCADE",
      });
    }

    // Cambiar user_id a NOT NULL en 'data_access_logs' si es nullable
    const tableLogs = await queryInterface.describeTable("data_access_logs");
    if (tableLogs.user_id && tableLogs.user_id.allowNull === true) {
      await queryInterface.changeColumn("data_access_logs", "user_id", {
        type: Sequelize.UUID,
        allowNull: false,
        references: {
          model: "users",
          key: "id",
        },
        onDelete: "CASCADE",
      });
    }

    // Eliminar claves foráneas duplicadas en 'files' (owner_id)
    await queryInterface.sequelize.query(`
      ALTER TABLE files
      DROP CONSTRAINT IF EXISTS files_owner_id_fkey1;
    `);

    // Eliminar claves foráneas duplicadas en 'folders' (owner_id)
    await queryInterface.sequelize.query(`
      ALTER TABLE folders
      DROP CONSTRAINT IF EXISTS folders_owner_id_fkey1;
    `);
  },

  down: async (queryInterface, Sequelize) => {
    // Revertir cambios a nullable para columnas
    await queryInterface.changeColumn("files", "owner_id", {
      type: Sequelize.UUID,
      allowNull: true,
      references: {
        model: "users",
        key: "id",
      },
      onDelete: "CASCADE",
    });

    await queryInterface.changeColumn("folders", "owner_id", {
      type: Sequelize.UUID,
      allowNull: true,
      references: {
        model: "users",
        key: "id",
      },
      onDelete: "CASCADE",
    });

    await queryInterface.changeColumn("data_access_logs", "user_id", {
      type: Sequelize.UUID,
      allowNull: true,
      references: {
        model: "users",
        key: "id",
      },
      onDelete: "CASCADE",
    });

    // No se restaura columna 'name' ni claves duplicadas en down
  },
};
