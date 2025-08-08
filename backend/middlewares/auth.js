const express = require("express");
const router = express.Router();
const jwt = require("jsonwebtoken");
const multer = require("multer");
const path = require("path");
const ocrController = require("../controllers/ocrController");
const logger = require("../config/logger");

const JWT_SECRET = process.env.JWT_SECRET || "secret_baseball";

// Middleware de autenticación JWT
const authMiddleware = (req, res, next) => {
  const authHeader = req.headers.authorization;
  if (!authHeader) {
    logger.warn("Token requerido en la petición");
    return res.status(401).json({ error: "Token requerido" });
  }

  const token = authHeader.split(" ")[1];
  if (!token) {
    logger.warn("Token no proporcionado");
    return res.status(401).json({ error: "Token no proporcionado" });
  }

  try {
    const decoded = jwt.verify(token, JWT_SECRET);
    req.user = decoded;
    next();
  } catch (err) {
    if (err.name === "TokenExpiredError") {
      logger.warn("Token expirado");
      return res.status(401).json({ error: "Token expirado" });
    }
    logger.warn(`Token inválido: ${err.message}`);
    return res.status(403).json({ error: "Token inválido" });
  }
};

// Multer configuración segura y saneamiento de nombre de archivo
const ALLOWED_MIME_TYPES = [
  "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
  "application/vnd.ms-excel",
  "text/csv",
];
const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10MB

const storage = multer.diskStorage({
  destination: (req, file, cb) => {
    const dir = path.resolve(__dirname, "../uploads");
    cb(null, dir);
  },
  filename: (req, file, cb) => {
    const ext = path.extname(file.originalname);
    // Sanitizar nombre reemplazando espacios y eliminando caracteres especiales
    const name = path
      .basename(file.originalname, ext)
      .replace(/\s+/g, "_")
      .replace(/[^\w\-]/g, "");
    const filename = `${Date.now()}_${name}${ext}`;
    logger.info(`Archivo guardado en uploads: ${filename}`);
    cb(null, filename);
  },
});

const fileFilter = (req, file, cb) => {
  if (ALLOWED_MIME_TYPES.includes(file.mimetype)) {
    cb(null, true);
  } else {
    logger.warn(
      `Archivo rechazado por tipo MIME no permitido: ${file.mimetype}`
    );
    cb(new Error("Tipo de archivo no permitido"), false);
  }
};

const upload = multer({
  storage,
  fileFilter,
  limits: { fileSize: MAX_FILE_SIZE },
});

// Manejo de errores de multer en ruta
router.post(
  "/upload",
  authMiddleware,
  upload.single("file"),
  (err, req, res, next) => {
    if (err) {
      logger.warn(`Error al subir archivo: ${err.message}`);
      return res.status(400).json({ error: err.message });
    }
    next();
  },
  ocrController.processFile
);

module.exports = router;
