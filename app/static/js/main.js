// Mejora progresiva del login: el form ya funciona sin JS.
(function () {
  function initLoginForm() {
    var form = document.getElementById("login-form");
    if (!form) {
      return;
    }

    var usernameInput = document.getElementById("username");
    var passwordInput = document.getElementById("password");
    var submitBtn = document.getElementById("login-submit-btn");
    var submitLabel = document.getElementById("login-submit-label");
    var spinner = document.getElementById("login-spinner");
    var toggleVisibilityBtn = document.getElementById("toggle-password-visibility");
    var eyeOpenIcon = document.getElementById("icon-eye-open");
    var eyeClosedIcon = document.getElementById("icon-eye-closed");
    var numericToggle = document.getElementById("toggle-numeric-keypad");

    // Deshabilitado por JS, no en el HTML: sin JS el form sigue enviable.
    function updateSubmitState() {
      if (!usernameInput || !passwordInput || !submitBtn) {
        return;
      }
      var hasUsername = usernameInput.value.trim().length > 0;
      var hasPassword = passwordInput.value.length > 0;
      submitBtn.disabled = !(hasUsername && hasPassword);
    }

    if (usernameInput) {
      usernameInput.addEventListener("input", updateSubmitState);
    }
    if (passwordInput) {
      passwordInput.addEventListener("input", updateSubmitState);
    }
    updateSubmitState();

    // Mostrar/ocultar: cada error de tipeo consume un intento del bloqueo.
    if (toggleVisibilityBtn && passwordInput) {
      toggleVisibilityBtn.addEventListener("click", function () {
        var isCurrentlyHidden = passwordInput.type === "password";
        passwordInput.type = isCurrentlyHidden ? "text" : "password";
        toggleVisibilityBtn.setAttribute("aria-pressed", String(isCurrentlyHidden));
        toggleVisibilityBtn.setAttribute(
          "aria-label",
          isCurrentlyHidden ? "Ocultar contrasena" : "Mostrar contrasena"
        );
        if (eyeOpenIcon && eyeClosedIcon) {
          eyeOpenIcon.classList.toggle("hidden", isCurrentlyHidden);
          eyeClosedIcon.classList.toggle("hidden", !isCurrentlyHidden);
        }
        passwordInput.focus();
      });
    }

    // Toggle manual: detectarlo por username seria un oraculo de enumeracion.
    if (numericToggle && passwordInput) {
      numericToggle.addEventListener("change", function () {
        passwordInput.setAttribute("inputmode", numericToggle.checked ? "numeric" : "text");
      });
    }

    // Evita que un doble-tap por lag queme dos intentos del bloqueo.
    form.addEventListener("submit", function () {
      if (submitBtn) {
        submitBtn.disabled = true;
      }
      if (submitLabel) {
        submitLabel.textContent = "Entrando...";
      }
      if (spinner) {
        spinner.classList.remove("hidden");
      }
    });
  }

  document.addEventListener("DOMContentLoaded", initLoginForm);
})();
