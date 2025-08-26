const express = require("express");
const router = express.Router();
const fileController = require("../controllers/fileController");
const authMiddleware = require("../middlewares/auth");

router.get("/", authMiddleware, fileController.listFiles);

router.post("/", authMiddleware, fileController.uploadFileRecord);

//router.get("/view/:driveFileId", authMiddleware, fileController.viewDriveFile);

router.delete("/:id", authMiddleware, fileController.deleteFile);

module.exports = router;
