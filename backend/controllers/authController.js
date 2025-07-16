const bcrypt = require("bcrypt");
const jwt = require("jsonwebtoken");
const { User } = require("../models");

const JWT_SECRET = process.env.JWT_SECRET || "secret_baseball";

exports.generateJwtToken = (user) => {
  const payload = {
    id: user.id,
    role: user.role,
  };
  return jwt.sign(payload, JWT_SECRET, { expiresIn: "1d" });
};

exports.register = async (req, res) => {
  const { email, password } = req.body;
  try {
    const exists = await User.findOne({ where: { email } });
    if (exists) return res.status(400).json({ error: "Email ya registrado" });

    const hash = await bcrypt.hash(password, 10);
    const user = await User.create({ email, password_hash: hash });

    const token = exports.generateJwtToken(user);
    res.json({ token, user });
  } catch (err) {
    res.status(500).json({ error: "Error al registrar usuario" });
  }
};

exports.login = async (req, res) => {
  const { email, password } = req.body;
  try {
    const user = await User.findOne({ where: { email } });
    if (!user || !user.password_hash)
      return res.status(401).json({ error: "Credenciales inválidas" });

    const valid = await bcrypt.compare(password, user.password_hash);
    if (!valid)
      return res.status(401).json({ error: "Credenciales inválidas" });

    const token = exports.generateJwtToken(user);
    res.json({ token, user });
  } catch (err) {
    res.status(500).json({ error: "Error al iniciar sesión" });
  }
};

exports.getProfile = async (req, res) => {
  try {
    const user = await User.findByPk(req.user.id, {
      attributes: ["id", "email", "name", "role", "language"],
    });
    if (!user) return res.status(404).json({ error: "Usuario no encontrado" });
    res.json(user);
  } catch (err) {
    res.status(500).json({ error: "Error al obtener perfil" });
  }
};

exports.googleLogin = async (profile) => {
  let user = await User.findOne({ where: { google_id: profile.id } });
  if (!user) {
    user = await User.create({
      google_id: profile.id,
      email: profile.emails[0].value,
      name: profile.displayName,
      role: "user",
    });
  }
  const token = exports.generateJwtToken(user);
  return { token, user };
};

exports.googleOAuthCallback = async (req, res) => {
  try {
    const { token, user } = await exports.googleLogin(req.user);
    res.json({ token, user });
  } catch (err) {
    res.status(500).json({ error: "Error en autenticación con Google" });
  }
};
