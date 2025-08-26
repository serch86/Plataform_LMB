const bcrypt = require("bcrypt");
const jwt = require("jsonwebtoken");
const { User } = require("../models");
const logger = require("../config/logger"); // Corrección aquí
const Joi = require("joi");

// Secret JWT
const JWT_SECRET = process.env.JWT_SECRET || "secret_baseball";

// ===========================
// Esquemas Joi para validar y sanear entradas
// ===========================
const registerSchema = Joi.object({
  email: Joi.string().email().required().trim().lowercase(),
  password: Joi.string().min(8).required(),
});

const loginSchema = Joi.object({
  email: Joi.string().email().required().trim().lowercase(),
  password: Joi.string().required(),
});

// ===========================
// Generador de Token JWT
// ===========================
exports.generateJwtToken = (user) => {
  const payload = {
    id: user.id,
    role: user.role,
  };
  return jwt.sign(payload, JWT_SECRET, { expiresIn: "1d" });
};

// ===========================
// Registro de Usuario
// ===========================
exports.register = async (req, res) => {
  const { error, value } = registerSchema.validate(req.body, {
    stripUnknown: true,
  });
  if (error) {
    logger.warn(`Registro fallido por validación: ${error.message}`);
    return res.status(400).json({ error: "Datos inválidos" });
  }
  const { email, password } = value;

  try {
    const exists = await User.findOne({ where: { email } });
    if (exists) {
      logger.warn(`Registro fallido: email ya registrado (${email})`);
      return res.status(400).json({ error: "Email ya registrado" });
    }

    const hash = await bcrypt.hash(password, 10);
    const user = await User.create({ email, password_hash: hash });

    const token = exports.generateJwtToken(user);
    logger.info(`Usuario registrado: ${email}`);
    res.json({ token, user });
  } catch (err) {
    logger.error(`Register error: ${err.message}`);
    res.status(500).json({ error: "Error al registrar usuario" });
  }
};

// ===========================
// Inicio de Sesión
// ===========================
exports.login = async (req, res) => {
  const { error, value } = loginSchema.validate(req.body, {
    stripUnknown: true,
  });
  if (error) {
    logger.warn(`Login fallido por validación: ${error.message}`);
    return res.status(400).json({ error: "Datos inválidos" });
  }
  const { email, password } = value;

  logger.info(`Login start: ${email}`);

  try {
    const user = await User.findOne({ where: { email } });

    if (!user || !user.password_hash) {
      logger.warn(
        `Login fail: usuario no encontrado o sin password_hash (${email})`
      );
      return res.status(401).json({ error: "Credenciales inválidas" });
    }

    const valid = await bcrypt.compare(password, user.password_hash);
    if (!valid) {
      logger.warn(`Login fail: contraseña inválida (${email})`);
      return res.status(401).json({ error: "Credenciales inválidas" });
    }

    const token = exports.generateJwtToken(user);
    logger.info(`Login success: ${email}`);
    res.json({ token, user });
  } catch (err) {
    logger.error(`Login error: ${err.message}`);
    res.status(500).json({ error: "Error al iniciar sesión" });
  }
};

// ===========================
// Obtener Perfil de Usuario
// ===========================
exports.getProfile = async (req, res) => {
  try {
    const user = await User.findByPk(req.user.id, {
      attributes: ["id", "email", "name", "role", "language"],
    });

    if (!user) {
      logger.warn(`Perfil no encontrado para id: ${req.user.id}`);
      return res.status(404).json({ error: "Usuario no encontrado" });
    }

    res.json(user);
  } catch (err) {
    logger.error(`GetProfile error: ${err.message}`);
    res.status(500).json({ error: "Error al obtener perfil" });
  }
};

// ===========================
// Callback de Google OAuth
// ===========================
exports.googleOAuthCallback = async (req, res) => {
  try {
    const user = req.user;
    const token = exports.generateJwtToken(user);
    logger.info(`Google OAuth login exitoso: ${user.email || user.id}`);
    res.json({ token, user });
  } catch (err) {
    logger.error(`Google OAuth callback error: ${err.message}`);
    res.status(500).json({ error: "Error en autenticación con Google" });
  }
};
