# Plan de implementación - Módulo de pagos

## 1. Objetivo general

Automatizar el control de acceso según el estado de suscripción, integrando una pasarela de pago (Stripe).

---

## 2. App Móvil (React Native)

### Pantalla de suscripción

- [x] Mostrar estado actual de la suscripción (`activo` / `inactivo`)
- [x] Botón "Pagar suscripción"
- [x] Switch para simular estado
- [ ] Mostrar fecha de expiración o próxima renovación (una vez el backend lo proporcione)

### Control de acceso

- [x] Redirigir a `/suscripcion` si la suscripción es inactiva
- [x] Bloquear acceso a pantallas restringidas desde `_layout.tsx` (router)
- [ ] Ocultar o deshabilitar botones según estado (`roster`, `reportes`,)

### Integración WebView (Stripe Checkout)

- [ ] Llamar a `/create-checkout-session` desde el backend
- [ ] Abrir URL de Stripe en WebView
- [ ] Escuchar retorno o cierre de sesión de pago
- [ ] Actualizar el estado tras el pago (reconsulta a backend)

---

## 3. Backend (Node.js o Python)

### Endpoints requeridos

- [ ] `POST /create-checkout-session` → genera sesión de pago y URL
- [ ] `POST /webhook` → recibe notificación de Stripe
- [ ] `GET /subscription-status` → devuelve estado `activo/inactivo` y fechas

---

## 4. Almacenamiento

- [ ] Guardar estado de suscripción por `team_id`
- [ ] Guardar `payment_id`, fecha de pago, fecha de expiración

---

## 5. Consideraciones

- [ ] Soporte para múltiples usuarios por equipo (misma suscripción)
- [ ] Integrar alertas por expiración próxima
