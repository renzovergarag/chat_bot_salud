(function () {
  const root = document.querySelector(".saludbot");
  const messages = document.querySelector("#chatMessages");
  const form = document.querySelector("#chatForm");
  const input = document.querySelector("#chatInput");
  const submitButton = form.querySelector("button");
  const INACTIVITY_LIMIT_MS = 20 * 60 * 1000;

  const centroInicial = root.dataset.centro || "CESFAM Rodelillo";
  const userName = root.dataset.userName || "";
  const centrosSalud = [
    { id: "600", nombre: "Centro De Salud Familiar Laguna Verde" },
    { id: "605", nombre: "Centro De Salud Familiar Placilla (Valparaíso)" },
    { id: "610", nombre: "Centro De Salud Familiar Placeres" },
    { id: "615", nombre: "Centro De Salud Familiar Barón" },
    { id: "620", nombre: "Centro De Salud Familiar Rodelillo" },
    { id: "621", nombre: "Centro De Salud Familiar Padre Damián Molokai" },
    { id: "625", nombre: "Centro De Salud Familiar Quebrada Verde" },
    { id: "630", nombre: "Centro De Salud Familiar Las Cañas" },
    { id: "635", nombre: "Centro De Salud Familiar Mena" },
    { id: "640", nombre: "Centro De Salud Familiar Puertas Negras" },
    { id: "645", nombre: "Centro De Salud Familiar Cordillera" },
    { id: "650", nombre: "Centro De Salud Familiar Esperanza" },
    { id: "655", nombre: "Centro De Salud Familiar Reina Isabel II" },
  ];

  const state = {
    index: 0,
    data: {},
    selectedCentroName: centroInicial,
    waiting: false,
    complete: false,
    submitting: false,
  };

  const steps = [
    {
      field: "motivo",
      prompt: "Cuéntame el motivo principal de tu consulta de morbilidad.",
      validate: minLength("Describe el motivo de consulta con al menos 3 caracteres.", 3),
    },
    {
      field: "detalle_sintomas",
      prompt: "Gracias. Ahora describe tus síntomas, desde cuándo comenzaron y si han cambiado.",
      validate: minLength("Describe tus síntomas con al menos 20 caracteres para orientar mejor la atención.", 20),
    },
    {
      field: "rut",
      prompt: "Indícame tu RUT. Ejemplo: 12.345.678-9.",
      validate(value) {
        return isValidRut(value)
          ? null
          : "El RUT ingresado no es válido. Usa el formato 12.345.678-9.";
      },
      transform: normalizeRutForStorage,
    },
    {
      field: "nombre",
      prompt: "Perfecto. Indícame tu nombre completo.",
      validate: validateFullName,
      skip() {
        return Boolean(userName);
      },
      defaultValue() {
        return userName;
      },
    },
    {
      field: "edad",
      prompt: "¿Cuál es tu edad?",
      validate(value) {
        const number = Number(value);
        return Number.isInteger(number) && number >= 0 && number <= 120
          ? null
          : "Ingresa una edad válida entre 0 y 120.";
      },
      transform(value) {
        return Number(value);
      },
    },
    {
      field: "telefono",
      prompt: "Indícame un teléfono de contacto. Ejemplo: +56912345678.",
      validate(value) {
        return /^\+569\d{8}$/.test(value.trim())
          ? null
          : "Ingresa un teléfono válido con formato +56912345678.";
      },
    },
    {
      field: "centro_salud",
      prompt: "Selecciona el CESFAM donde quieres orientar esta solicitud.",
      options: centrosSalud,
      validate(value) {
        return centrosSalud.some((centro) => centro.id === value)
          ? null
          : "Selecciona una opción de CESFAM de la lista.";
      },
      display(value) {
        return centrosSalud.find((centro) => centro.id === value)?.nombre || value;
      },
    },
    {
      field: "credendencial_cuidador_discapacidad",
      prompt: "¿Cuentas con credencial de discapacidad o eres cuidador/a?",
      options: [
        { id: "true", nombre: "Sí" },
        { id: "false", nombre: "No" },
      ],
      validate: validateBooleanOption,
      transform: valueToBoolean,
      display: displayBooleanOption,
    },
    {
      field: "Neurodivergente_prais_gestante",
      prompt: "¿Eres persona neurodivergente, PRAIS o gestante?",
      options: [
        { id: "true", nombre: "Sí" },
        { id: "false", nombre: "No" },
      ],
      validate: validateBooleanOption,
      transform: valueToBoolean,
      display: displayBooleanOption,
    },
  ];

  function minLength(message, length) {
    return (value) => (value.trim().length >= length ? null : message);
  }

  function validateFullName(value) {
    const words = value.trim().split(/\s+/).filter(Boolean);
    if (value.trim().length < 8 || words.length < 2) {
      return "Ingresa tu nombre completo, con nombre y apellido.";
    }
    return null;
  }

  function validateBooleanOption(value) {
    return ["true", "false"].includes(value) ? null : "Selecciona Sí o No para continuar.";
  }

  function valueToBoolean(value) {
    return value === "true";
  }

  function displayBooleanOption(value) {
    return value === "true" ? "Sí" : "No";
  }

  function botIcon() {
    return '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M10 3h4v5h5v4h-5v5h-4v-5H5V8h5V3Zm-5 17h14v-2H5v2Z"/></svg>';
  }

  function userIcon() {
    return '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 12a4 4 0 1 0 0-8 4 4 0 0 0 0 8Zm-7 9a7 7 0 0 1 14 0H5Z"/></svg>';
  }

  function addMessage(content, sender, options) {
    const row = document.createElement("div");
    row.className = `message message--${sender}`;

    const leftAvatar = document.createElement("div");
    leftAvatar.className = "avatar";
    leftAvatar.innerHTML = botIcon();

    const rightAvatar = document.createElement("div");
    rightAvatar.className = "avatar avatar--user";
    rightAvatar.innerHTML = userIcon();

    const spacer = document.createElement("div");
    const bubble = document.createElement("div");
    bubble.className = "bubble";

    if (options && options.html) {
      bubble.innerHTML = content;
    } else {
      bubble.textContent = content;
    }

    if (sender === "user") {
      row.append(spacer, bubble, rightAvatar);
    } else {
      row.append(leftAvatar, bubble, spacer);
    }

    messages.appendChild(row);
    scrollToLatest(row);
    return row;
  }

  function scrollToLatest(target) {
    window.requestAnimationFrame(() => {
      messages.scrollTo({
        top: Math.max(messages.scrollHeight - messages.clientHeight + 24, 0),
        behavior: "smooth",
      });
      window.setTimeout(() => {
        const element = target || messages.lastElementChild;
        if (!element) return;

        element.scrollIntoView({
          behavior: "smooth",
          block: "nearest",
          inline: "nearest",
        });
      }, 80);
    });
  }

  function showTyping(callback) {
    state.waiting = true;
    input.disabled = true;
    submitButton.disabled = true;

    const row = addMessage('<span class="typing">SaludBot está escribiendo...</span>', "bot", { html: true });
    window.setTimeout(() => {
      row.remove();
      state.waiting = false;
      input.disabled = false;
      submitButton.disabled = false;
      callback();
      scrollToLatest();
      input.focus();
    }, 520);
  }

  function askCurrentStep() {
    const step = steps[state.index];

    if (!step) {
      showSummary();
      return;
    }

    if (step.skip && step.skip()) {
      state.data[step.field] = step.defaultValue();
      state.index += 1;
      askCurrentStep();
      return;
    }

    let prompt = step.prompt;
    if (step.defaultHint) {
      prompt += ` Puedes confirmar escribiendo "${step.defaultHint()}".`;
    }

    if (step.options) {
      prompt += renderOptionButtons(step.options);
    }

    showTyping(() => addMessage(prompt, "bot", { html: Boolean(step.options) }));
  }

  function quickActions() {
    const actions = ["Tengo fiebre", "Dolor o malestar", "Síntomas respiratorios", "Control o medicamento", "Otra consulta"];
    return `
      <div class="quick-actions" aria-label="Opciones rapidas">
        ${actions.map((label) => `<button class="quick-action" type="button" data-value="${escapeAttr(label)}">${escapeHtml(label)}</button>`).join("")}
      </div>
    `;
  }

  function renderOptionButtons(options) {
    return `
      <div class="quick-actions quick-actions--list" aria-label="Opciones de CESFAM">
        ${options
          .map(
            (option) =>
              `<button class="quick-action quick-action--wide" type="button" data-value="${escapeAttr(option.id)}" data-label="${escapeAttr(option.nombre)}">${escapeHtml(option.nombre)}</button>`
          )
          .join("")}
      </div>
    `;
  }

  function start() {
    const greetingName = userName ? `, ${escapeHtml(userName)}` : "";
    addMessage(
      `Hola 👋 Soy SaludBot${greetingName}, asistente virtual de salud familiar. Te ayudaré a seleccionar el motivo de morbilidad y recopilar la información necesaria para tu atención.${quickActions()}`,
      "bot",
      { html: true }
    );
    resetInactivityTimer();
  }

  function showSummary() {
    state.complete = true;
    input.disabled = true;
    submitButton.disabled = true;

    const summary = `
      <strong>Revisa los datos antes de continuar.</strong>
      <div class="summary">
        <div class="summary__item"><span>Motivo</span><strong>${escapeHtml(state.data.motivo)}</strong></div>
        <div class="summary__item"><span>Síntomas</span><strong>${escapeHtml(state.data.detalle_sintomas)}</strong></div>
        <div class="summary__item"><span>RUT</span><strong>${escapeHtml(state.data.rut)}</strong></div>
        <div class="summary__item"><span>Nombre</span><strong>${escapeHtml(state.data.nombre)}</strong></div>
        <div class="summary__item"><span>Edad</span><strong>${escapeHtml(state.data.edad)}</strong></div>
        <div class="summary__item"><span>Teléfono</span><strong>${escapeHtml(state.data.telefono)}</strong></div>
        <div class="summary__item"><span>CESFAM</span><strong>${escapeHtml(state.selectedCentroName)}</strong></div>
        <div class="summary__item"><span>Credencial/cuidador</span><strong>${state.data.credendencial_cuidador_discapacidad ? "Sí" : "No"}</strong></div>
        <div class="summary__item"><span>Neurodivergente/PRAIS/gestante</span><strong>${state.data.Neurodivergente_prais_gestante ? "Sí" : "No"}</strong></div>
      </div>
      <div class="summary-actions">
        <button class="summary-action" type="button" data-final-action="send">Confirmar y enviar</button>
        <button class="summary-action" type="button" data-final-action="restart">Corregir datos</button>
      </div>
    `;

    showTyping(() => addMessage(summary, "bot", { html: true }));
  }

  function restart() {
    state.index = 0;
    state.complete = false;
    state.data = {};
    state.selectedCentroName = centroInicial;
    state.waiting = false;
    state.submitting = false;
    messages.innerHTML = "";
    input.disabled = false;
    submitButton.disabled = false;
    input.value = "";
    start();
    scrollToLatest();
  }

  function resetByInactivity() {
    if (state.complete || state.index === 0) {
      resetInactivityTimer();
      return;
    }

    state.index = 0;
    state.complete = false;
    state.data = {};
    state.selectedCentroName = centroInicial;
    state.waiting = false;
    state.submitting = false;
    messages.innerHTML = "";
    input.disabled = false;
    submitButton.disabled = false;
    input.value = "";
    addMessage("La conversación se reinició por inactividad de 20 minutos.", "bot");
    start();
  }

  let inactivityTimer = window.setTimeout(resetByInactivity, INACTIVITY_LIMIT_MS);

  function resetInactivityTimer() {
    window.clearTimeout(inactivityTimer);
    inactivityTimer = window.setTimeout(resetByInactivity, INACTIVITY_LIMIT_MS);
  }

  async function finish() {
    if (state.submitting) return;
    state.submitting = true;
    resetInactivityTimer();
    input.disabled = true;
    submitButton.disabled = true;
    addMessage("Estoy registrando tu solicitud en el sistema.", "bot");

    const payload = {
      rut: state.data.rut,
      edad: state.data.edad,
      telefono: state.data.telefono,
      centro_salud: state.data.centro_salud,
      credendencial_cuidador_discapacidad: state.data.credendencial_cuidador_discapacidad,
      Neurodivergente_prais_gestante: state.data.Neurodivergente_prais_gestante,
      motivo: state.data.motivo,
      detalle_motivo: state.data.detalle_sintomas,
    };

    try {
      const response = await fetch("/api/solicitudes/", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": getCsrfToken(),
        },
        body: JSON.stringify(payload),
      });
      const result = await response.json();

      if (!response.ok) {
        addMessage(`<span class="error">No se pudo guardar la solicitud.</span><br>${formatErrors(result.errors)}`, "bot", { html: true });
        askAnotherSolicitud();
        return;
      }

      addMessage(
        `Solicitud registrada correctamente.<br><br><strong>ID de solicitud:</strong> ${result.id_solicitud}<br><strong>RUT:</strong> ${escapeHtml(result.resumen.rut)}<br><strong>Centro de salud:</strong> ${escapeHtml(result.resumen.centro_salud_nombre || state.selectedCentroName)}<br><strong>Edad:</strong> ${escapeHtml(result.resumen.edad)}`,
        "bot",
        { html: true }
      );
      askAnotherSolicitud();
    } catch (error) {
      addMessage('<span class="error">No se pudo conectar con el servidor. Intenta nuevamente.</span>', "bot", { html: true });
      askAnotherSolicitud();
    }
  }

  function askAnotherSolicitud() {
    addMessage(
      `¿Deseas realizar otra solicitud?
      <div class="summary-actions">
        <button class="summary-action" type="button" data-post-action="restart">Sí</button>
        <button class="summary-action" type="button" data-post-action="close">No</button>
      </div>`,
      "bot",
      { html: true }
    );
  }

  function closeConversation() {
    input.disabled = true;
    submitButton.disabled = true;
    input.placeholder = "La conversación ha finalizado.";
    addMessage("Gracias. La conversación ha finalizado.", "bot");
  }

  function disableSiblingActions(button) {
    const container = button.closest(".summary-actions");
    if (!container) return;

    container.querySelectorAll("button").forEach((actionButton) => {
      actionButton.disabled = true;
      actionButton.setAttribute("aria-disabled", "true");
    });
  }

  function submitValue(value) {
    resetInactivityTimer();
    const step = steps[state.index];
    const error = step.validate(value);
    const displayValue = step.display ? step.display(value) : value;
    addMessage(displayValue, "user");

    if (error) {
      showTyping(() => addMessage(`<span class="error">${escapeHtml(error)}</span>`, "bot", { html: true }));
      return;
    }

    state.data[step.field] = step.transform ? step.transform(value) : value.trim();
    if (step.field === "centro_salud") {
      state.selectedCentroName = displayValue;
    }
    state.index += 1;
    askCurrentStep();
  }

  function isValidRut(value) {
    const rut = value.trim();
    if (!/^\d{1,2}\.\d{3}\.\d{3}-[\dkK]$/.test(rut)) return false;

    const clean = rut.replace(/\./g, "").replace("-", "").toUpperCase();
    const body = clean.slice(0, -1);
    const checkDigit = clean.slice(-1);
    const factors = [2, 3, 4, 5, 6, 7];
    let sum = 0;

    Array.from(body).reverse().forEach((digit, index) => {
      sum += Number(digit) * factors[index % factors.length];
    });

    const result = 11 - (sum % 11);
    const expected = result === 11 ? "0" : result === 10 ? "K" : String(result);
    return checkDigit === expected;
  }

  function normalizeRutForStorage(value) {
    const clean = value.replace(/\./g, "").replace("-", "").toUpperCase();
    return `${clean.slice(0, -1)}-${clean.slice(-1)}`;
  }

  function formatErrors(errors) {
    if (Array.isArray(errors)) return errors.map(escapeHtml).join("<br>");
    return Object.entries(errors || {})
      .map(([field, values]) => `${escapeHtml(field)}: ${values.map(escapeHtml).join(", ")}`)
      .join("<br>");
  }

  function getCsrfToken() {
    const csrfInput = document.querySelector("[name=csrfmiddlewaretoken]");
    if (csrfInput) return csrfInput.value;

    const cookie = document.cookie
      .split(";")
      .map((item) => item.trim())
      .find((item) => item.startsWith("csrftoken="));
    return cookie ? decodeURIComponent(cookie.split("=").slice(1).join("=")) : "";
  }

  function escapeHtml(value) {
    return String(value)
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#039;");
  }

  function escapeAttr(value) {
    return escapeHtml(value).replaceAll("`", "&#096;");
  }

  form.addEventListener("submit", (event) => {
    event.preventDefault();
    if (state.waiting || state.complete) return;

    const value = input.value.trim();
    if (!value) return;

    input.value = "";
    submitValue(value);
  });

  messages.addEventListener("click", (event) => {
    resetInactivityTimer();
    const quickButton = event.target.closest("[data-value]");
    const finalButton = event.target.closest("[data-final-action]");
    const postButton = event.target.closest("[data-post-action]");

    if (quickButton && !state.waiting && !state.complete) {
      submitValue(quickButton.dataset.value);
      return;
    }

    if (postButton) {
      disableSiblingActions(postButton);
      if (postButton.dataset.postAction === "restart") {
        restart();
      } else {
        closeConversation();
      }
      return;
    }

    if (!finalButton || finalButton.disabled) return;

    disableSiblingActions(finalButton);
    if (finalButton.dataset.finalAction === "restart") {
      restart();
    } else {
      finish();
    }
  });

  start();
})();
