const passport = require("passport");
const GoogleStrategy = require("passport-google-oauth20").Strategy;
const { User } = require("../models");

passport.use(
  new GoogleStrategy(
    {
      clientID: process.env.GOOGLE_CLIENT_ID,
      clientSecret: process.env.GOOGLE_CLIENT_SECRET,
      callbackURL: process.env.GOOGLE_CALLBACK_URL,
    }, // Se ejecuta después de la autenticación con Google
    async (accessToken, refreshToken, profile, done) => {
      try {
        // Validación segura del email
        const email =
          profile.emails && profile.emails[0] && profile.emails[0].value;
        if (!email) return done(new Error("No email from Google"), null);

        // Busca si ya existe un usuario con este google_id en la base de datos
        const user = await User.findOne({ where: { google_id: profile.id } });

        // Si no existe, falla la autenticación
        if (!user) return done(null, false, { message: "USER_NOT_FOUND" });

        // Usuario encontrado, se completa la autenticación
        return done(null, user);
      } catch (err) {
        // En caso de error, lo pasa al manejador de Passport
        return done(err, null);
      }
    }
  )
);

module.exports = passport;
