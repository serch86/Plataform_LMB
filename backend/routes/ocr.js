const express = require("express");
const router = express.Router();
const multer = require("multer");
const path = require("path");
const ocrController = require("../controllers/ocrController");

// almacenamiento de multer
const storage = multer.diskStorage({
  destination: (req, file, cb) => {
    const dir = path.resolve(__dirname, "../uploads"); // carpeta uploads en raíz
    cb(null, dir);
  },
  filename: (req, file, cb) => {
    const ext = path.extname(file.originalname);
    const name = path.basename(file.originalname, ext).replace(/\s+/g, "_");
    const filename = `${Date.now()}_${name}${ext}`;
    console.log("Archivo guardado en uploads:", filename);
    cb(null, filename);
  },
});

const upload = multer({ storage });

// Endpoint para subir archivo y procesar OCR
router.post("/upload", upload.single("file"), ocrController.processFile);

module.exports = router;
