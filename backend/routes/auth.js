const express = require("express");
const router = express.Router();
const authController = require("../controllers/authController");
const authMiddleware = require("../middlewares/auth");
const passport = require("passport");

router.post("/register", authController.register);

router.post("/login", authController.login);

router.get("/profile", authMiddleware, authController.getProfile);

router.get(
  "/google",
  (req, res, next) => {
    console.log("Entrando a /google");
    next();
  },
  passport.authenticate("google", {
    scope: ["profile", "email"],
  })
);

router.get(
  "/google/callback",
  passport.authenticate("google", {
    session: false,
    failureRedirect: "/login",
  }),
  authController.googleOAuthCallback
);

module.exports = router;
