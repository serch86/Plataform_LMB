const { File, User } = require("../models");
const path = require("path");
const fs = require("fs");
const logger = require("../config/logger");

// Tipos MIME permitidos y tamaño máximo (10 MB)
const ALLOWED_MIME_TYPES = [
  "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
  "application/vnd.ms-excel",
  "text/csv",
];
const MAX_FILE_SIZE = 10 * 1024 * 1024;

// ===========================
// Lista archivos del usuario actual
// ===========================
exports.listFiles = async (req, res) => {
  if (!req.user || !req.user.id) {
    logger.warn("Usuario no autenticado al listar archivos");
    return res.status(401).json({ error: "No autenticado" });
  }
  try {
    const files = await File.findAll({ where: { owner_id: req.user.id } });
    logger.info(`Archivos listados para usuario: ${req.user.id}`);
    res.json(files);
  } catch (err) {
    logger.error(
      `Error al listar archivos usuario ${
        req.user ? req.user.id : "desconocido"
      }: ${err.message}`
    );
    res.status(500).json({ error: "No se pudo listar archivos" });
  }
};

// ===========================
// Guarda registro del archivo subido con validación
// ===========================
exports.uploadFileRecord = async (req, res) => {
  if (!req.user || !req.user.id) {
    logger.warn("Usuario no autenticado en uploadFileRecord");
    return res.status(401).json({ error: "No autenticado" });
  }

  if (!req.file) {
    logger.warn("No se recibió ningún archivo en uploadFileRecord");
    return res.status(400).json({ error: "No se recibió ningún archivo" });
  }

  // Validar tipo MIME
  if (!ALLOWED_MIME_TYPES.includes(req.file.mimetype)) {
    logger.warn(`Tipo MIME no permitido: ${req.file.mimetype}`);
    return res.status(400).json({ error: "Tipo de archivo no permitido" });
  }

  // Validar tamaño
  if (req.file.size > MAX_FILE_SIZE) {
    logger.warn(`Archivo demasiado grande: ${req.file.size} bytes`);
    return res.status(400).json({ error: "Archivo demasiado grande" });
  }

  // Validar nombre de archivo (sanear)
  const originalname = path
    .basename(req.file.originalname)
    .replace(/[^\w.\-]/g, "");

  try {
    const file = await File.create({
      drive_file_id: null,
      name: originalname,
      type: req.file.mimetype,
      bigquery_table: null,
      owner_id: req.user.id,
    });

    logger.info(
      `Archivo registrado: ${originalname} para usuario ${req.user.id}`
    );
    res.status(201).json({ file, message: "Archivo subido correctamente" });
  } catch (err) {
    logger.error(
      `Error al guardar archivo usuario ${req.user.id}: ${err.message}`
    );
    res.status(500).json({ error: "No se pudo guardar archivo" });
  }
};

// ===========================
// Elimina archivo por ID con validación de ID
// ===========================
exports.deleteFile = async (req, res) => {
  if (!req.user || !req.user.id) {
    logger.warn("Usuario no autenticado en deleteFile");
    return res.status(401).json({ error: "No autenticado" });
  }

  const id = req.params.id;

  // Validar formato ID (UUID esperado)
  const uuidRegex =
    /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
  if (!uuidRegex.test(id)) {
    logger.warn(`ID archivo inválido para eliminar: ${id}`);
    return res.status(400).json({ error: "ID inválido" });
  }

  try {
    const file = await File.findByPk(id);
    if (!file) {
      logger.warn(`Archivo no encontrado para eliminar: ID ${id}`);
      return res.status(404).json({ error: "Archivo no encontrado" });
    }

    if (file.owner_id !== req.user.id) {
      logger.warn(
        `Intento no autorizado de eliminar archivo ID ${id} por usuario ${req.user.id}`
      );
      return res.status(403).json({ error: "No autorizado" });
    }

    await file.destroy();

    logger.info(`Archivo eliminado: ID ${id} por usuario ${req.user.id}`);
    res.status(200).json({ message: "Archivo eliminado" });
  } catch (err) {
    logger.error(`Error al eliminar archivo ID ${id}: ${err.message}`);
    res.status(500).json({ error: "Error al eliminar archivo" });
  }
};
