const { File, User } = require("../models");
const drive = require("../services/drive");

exports.listFiles = async (req, res) => {
  try {
    const files = await File.findAll({ where: { owner_id: req.user.id } });
    res.json(files);
  } catch (err) {
    res.status(500).json({ error: "No se pudo listar archivos" });
  }
};

exports.uploadFileRecord = async (req, res) => {
  const { drive_file_id, name, type, bigquery_table } = req.body;
  try {
    const file = await File.create({
      drive_file_id,
      name,
      type,
      bigquery_table,
      owner_id: req.user.id,
    });
    res.status(201).json(file);
  } catch (err) {
    res.status(500).json({ error: "No se pudo guardar archivo" });
  }
};

exports.deleteFile = async (req, res) => {
  const { id } = req.params;
  try {
    const file = await File.findByPk(id);
    if (!file) return res.status(404).json({ error: "Archivo no encontrado" });

    await file.destroy();
    res.status(200).json({ message: "Archivo eliminado" });
  } catch (err) {
    res.status(500).json({ error: "Error al eliminar archivo" });
  }
};

exports.viewDriveFile = async (req, res) => {
  const { driveFileId } = req.params;
  try {
    const response = await drive.files.get(
      { fileId: driveFileId, alt: "media" },
      { responseType: "stream" }
    );

    res.setHeader("Content-Type", "application/octet-stream");
    response.data.pipe(res);
  } catch (err) {
    res.status(500).json({ error: "No se pudo leer archivo desde Drive" });
  }
};
