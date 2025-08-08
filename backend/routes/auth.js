const express = require("express");
const router = express.Router();
const authController = require("../controllers/authController");
const authMiddleware = require("../middlewares/auth");
const passport = require("passport");

// --- Autenticación Tradicional ---
router.post("/login", authController.login); // Ruta para el inicio de sesión con credenciales

router.get("/profile", authMiddleware, authController.getProfile); // Ruta protegida para obtener el perfil del usuario

// --- Autenticación con Google OAuth ---

// Inicia el flujo de autenticación con Google
router.get(
  "/google",
  (req, res, next) => {
    console.log("Entrando a /google para iniciar OAuth"); // Log de depuración
    next();
  },
  passport.authenticate("google", {
    scope: ["profile", "email"], // Solicita acceso al perfil y email del usuario
  })
);

// Callback de Google después de la autenticación
router.get("/google/callback", (req, res, next) => {
  // Autentica con Passport y sin sesiones (para JWT)
  passport.authenticate("google", { session: false }, (err, user) => {
    if (err) {
      console.error("Error de autenticación:", err.message); // Log del error
      // Redirige al frontend con mensaje de error
      return res.redirect(
        `front://login?error=${encodeURIComponent(err.message)}`
      );
    }

    if (!user) {
      // Redirige si el usuario no fue autenticado por Passport (ej. no encontrado en BD)
      return res.redirect(`front://login?error=Acceso%20denegado`);
    }

    // Pasa el usuario autenticado al controlador para generar JWT y redirigir
    req.user = user;
    authController.googleOAuthCallback(req, res);
  })(req, res, next); // Asegura que el middleware de Passport se ejecute con req, res, next
});

module.exports = router;
