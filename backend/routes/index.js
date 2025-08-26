const express = require("express");
const router = express.Router();

router.use("/auth", require("./auth"));
router.use("/files", require("./files"));
router.use("/ocr", require("./ocr"));

module.exports = router;
