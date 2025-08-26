const fs = require("fs");
const path = require("path");
const { spawn } = require("child_process");
const logger = require("../config/logger");
const { sequelize, File } = require("../models");

const ALLOWED_MIME_TYPES = [
  "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
  "application/vnd.ms-excel",
  "text/csv",
];
const MAX_FILE_SIZE = 10 * 1024 * 1024;

exports.processFile = async (req, res) => {
  logger.info(
    `Archivo recibido por multer: ${
      req.file ? req.file.originalname : "ninguno"
    }`
  );

  if (!req.file) {
    logger.warn("No se recibió ningún archivo");
    return res.status(400).json({ error: "No se recibió ningún archivo" });
  }

  if (!ALLOWED_MIME_TYPES.includes(req.file.mimetype)) {
    logger.warn(`Tipo MIME no permitido: ${req.file.mimetype}`);
    return res.status(400).json({ error: "Tipo de archivo no permitido" });
  }

  if (req.file.size > MAX_FILE_SIZE) {
    logger.warn(`Archivo demasiado grande: ${req.file.size} bytes`);
    return res.status(400).json({ error: "Archivo demasiado grande" });
  }

  const sanitizedFileName = path
    .basename(req.file.originalname)
    .replace(/[^\w.\-]/g, "");
  const filePath = path.resolve(req.file.path);

  try {
    const pythonScriptPath = path.resolve(
      __dirname,
      "../services/python_scripts/extract_metadata.py"
    );
    const pythonExecutablePath =
      "/home/yael/Desktop/proyectos_web/baseball/Plataform_LMB/backend/back_app_baseball/env/bin/python3";

    const pythonProcess = spawn(pythonExecutablePath, [
      pythonScriptPath,
      filePath,
    ]);

    let pythonOutput = "";
    let pythonError = "";

    pythonProcess.stdout.on("data", (data) => {
      const message = data.toString();
      logger.info(`[Python stdout] ${message}`);
      pythonOutput += message;
    });

    pythonProcess.stderr.on("data", (data) => {
      const message = data.toString();
      logger.error(`[Python stderr] ${message}`);
      pythonError += message;
    });

    await new Promise((resolve, reject) => {
      pythonProcess.on("close", (code) => {
        if (code !== 0) {
          logger.error(
            `Script de Python salió con código ${code}: ${pythonError}`
          );
          reject(
            new Error(
              `Error al ejecutar el script de metadatos: ${
                pythonError || "Código de salida no cero"
              }`
            )
          );
        } else {
          resolve();
        }
      });
      pythonProcess.on("error", (err) => {
        logger.error(`Falló al iniciar el script de Python: ${err.message}`);
        reject(
          new Error(`Falló al iniciar el script de Python: ${err.message}`)
        );
      });
    });

    const metadata = JSON.parse(pythonOutput);
    const fileKey = Object.keys(metadata)[0];
    const contenido = metadata[fileKey] || {};

    // No se guarda nada en la base de datos ni en transaction

    res.json({
      message: "Archivo procesado correctamente.",
      archivo: {
        nombre: fileKey,
        tamaño_bytes: req.file.size,
        extension: path.extname(fileKey).replace(".", ""),
        tipo: req.file.mimetype,
      },
      datos_extraidos: contenido.datos_extraidos || {},
      tablas: contenido.tables || [],
    });
  } catch (err) {
    logger.error(`Error al procesar archivo: ${err.message}`);
    res
      .status(500)
      .json({ error: err.message || "Error interno al procesar archivo." });
  } finally {
    fs.unlink(filePath, (unlinkErr) => {
      if (unlinkErr) {
        logger.error(
          `Error al eliminar archivo temporal: ${unlinkErr.message}`
        );
      } else {
        logger.info(`Archivo temporal eliminado: ${filePath}`);
      }
    });
  }
};
