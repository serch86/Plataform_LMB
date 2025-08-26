const { google } = require("googleapis");
const path = require("path");
const logger = require("../config/logger"); // Uso del logger centralizado

const keyPath = path.join(__dirname, "../../key.json");

const auth = new google.auth.GoogleAuth({
  keyFile: keyPath,
  scopes: ["https://www.googleapis.com/auth/drive.readonly"],
});

auth
  .getClient()
  .then(() => logger.info("Google Drive Authenticated"))
  .catch((err) => logger.error("Error authenticating Google Drive:", err));

const drive = google.drive({ version: "v3", auth });

module.exports = drive;
