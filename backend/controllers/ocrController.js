const fs = require("fs");
const path = require("path");
const Tesseract = require("tesseract.js");

exports.processFile = async (req, res) => {
  if (!req.file) {
    return res.status(400).json({ error: "No se recibió ningún archivo" });
  }

  const filePath = path.resolve(req.file.path);

  try {
    const {
      data: { text },
    } = await Tesseract.recognize(filePath, "eng");

    // Extrae nombres
    const foundNames = text.match(/[A-Z][a-z]+ [A-Z][a-z]+/g) || [];

    // Limpia archivo temporal
    fs.unlinkSync(filePath);

    res.json({
      rawText: text,
      matches: foundNames,
    });
  } catch (err) {
    console.error("Error al procesar archivo:", err);
    res.status(500).json({ error: "Error al procesar OCR" });
  }
};
