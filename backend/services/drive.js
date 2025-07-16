const { google } = require("googleapis");
const path = require("path");

const keyPath = path.join(__dirname, "../../key.json");

const auth = new google.auth.GoogleAuth({
  keyFile: keyPath,
  scopes: ["https://www.googleapis.com/auth/drive.readonly"],
});

const drive = google.drive({ version: "v3", auth });

module.exports = drive;
