const messagesEl = document.querySelector("#messages");
const formEl = document.querySelector("#chatForm");
const inputEl = document.querySelector("#messageInput");

const state = {
  stepIndex: 0,
  finished: false,
  data: {},
};

const steps = [
  {
    field: "motivo",
    prompt: "Hola. Soy tu asistente virtual del CESFAM Rodelillo. Describe tu consulta o el motivo de tu visita.",
    validate: requiredText("Indica brevemente el motivo de tu consulta."),
  },
  {
    field: "detalle_motivo",
    prompt: "Entiendo. Para poder ayudarte mejor, describeme los sintomas o detalles de tu consulta.",
    validate: requiredText("Describe con un poco mas de detalle tu motivo de consulta."),
  },
  {
    field: "rut",
    prompt: "Gracias. Ahora, por favor, indicame tu RUT. Ejemplo: 12.345.678-9.",
    validate(value) {
      return validateRut(value) ? null : "El RUT ingresado no es valido. Usa el formato 12.345.678-9.";
    },
  },
  {
    field: "edad",
    prompt: "Gracias. Ahora, por favor, indicame tu edad.",
    validate(value) {
      const age = Number(value);
      return Number.isInteger(age) && age >= 0 && age <= 120 ? null : "Ingresa una edad valida entre 0 y 120.";
    },
    transform(value) {
      return Number(value);
    },
  },
  {
    field: "sexo",
    prompt: "Indica tu sexo: femenino, masculino, otro o prefiero no decir.",
    validate(value) {
      return normalizeSex(value) ? null : "Responde femenino, masculino, otro o prefiero no decir.";
    },
    transform: normalizeSex,
  },
  {
    field: "telefono",
    prompt: "Perfecto. Indica tu numero de telefono de contacto. Ejemplo: +56912345678.",
    validate(value) {
      return /^\+569\d{8}$/.test(value.trim()) ? null : "El telefono debe tener formato +56912345678.";
    },
  },
  {
    field: "centro_salud",
    prompt: "Indica tu centro de salud.",
    validate: requiredText("Indica el centro de salud al que perteneces."),
  },
  {
    field: "credendencial_cuidador_discapacidad",
    prompt: "¿Tienes credencial de discapacidad o eres cuidador/a? Responde si o no.",
    validate: yesNoValidation,
    transform: yesNoToBoolean,
  },
  {
    field: "Neurodivergente_prais_gestante",
    prompt: "¿Eres neurodivergente, PRAIS o gestante? Responde si o no.",
    validate: yesNoValidation,
    transform: yesNoToBoolean,
  },
];

function requiredText(message) {
  return (value) => (value.trim().length >= 2 ? null : message);
}

function yesNoValidation(value) {
  return parseYesNo(value) === null ? "Responde si o no." : null;
}

function parseYesNo(value) {
  const normalized = value.trim().toLowerCase();
  if (["si", "sí", "s", "yes", "y"].includes(normalized)) return true;
  if (["no", "n"].includes(normalized)) return false;
  return null;
}

function yesNoToBoolean(value) {
  return parseYesNo(value);
}

function normalizeSex(value) {
  const normalized = value.trim().toLowerCase();
  if (["f", "femenino", "mujer"].includes(normalized)) return "F";
  if (["m", "masculino", "hombre"].includes(normalized)) return "M";
  if (["o", "otro", "otra"].includes(normalized)) return "O";
  if (["n", "prefiero no decir", "no decir"].includes(normalized)) return "N";
  return null;
}

function validateRut(value) {
  if (!/^\d{1,2}\.\d{3}\.\d{3}-[\dkK]$/.test(value.trim())) return false;
  const clean = value.replace(/\./g, "").replace("-", "").toUpperCase();
  const body = clean.slice(0, -1);
  const checkDigit = clean.slice(-1);
  const factors = [2, 3, 4, 5, 6, 7];
  let sum = 0;

  [...body].reverse().forEach((digit, index) => {
    sum += Number(digit) * factors[index % factors.length];
  });

  const expectedValue = 11 - (sum % 11);
  const expected = expectedValue === 11 ? "0" : expectedValue === 10 ? "K" : String(expectedValue);
  return checkDigit === expected;
}

function addMessage(text, sender = "bot", html = false) {
  const row = document.createElement("div");
  row.className = `message-row ${sender}`;

  const botAvatar = document.createElement("div");
  botAvatar.className = "avatar";
  botAvatar.textContent = "▣";

  const userAvatar = document.createElement("div");
  userAvatar.className = "avatar user-avatar";
  userAvatar.textContent = "◉";

  const spacer = document.createElement("div");
  const bubble = document.createElement("div");
  bubble.className = "bubble";
  if (html) {
    bubble.innerHTML = text;
  } else {
    bubble.textContent = text;
  }

  if (sender === "user") {
    row.append(spacer, bubble, userAvatar);
  } else {
    row.append(botAvatar, bubble, spacer);
  }

  messagesEl.appendChild(row);
  messagesEl.scrollTop = messagesEl.scrollHeight;
}

function currentStep() {
  return steps[state.stepIndex];
}

function askCurrentStep() {
  addMessage(currentStep().prompt);
}

async function submitSolicitud() {
  inputEl.disabled = true;
  formEl.querySelector("button").disabled = true;
  addMessage("Gracias por tu informacion. Estoy registrando la solicitud.");

  const response = await fetch("/api/solicitudes/", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-CSRFToken": getCookie("csrftoken"),
    },
    body: JSON.stringify(state.data),
  });

  const result = await response.json();
  if (!response.ok) {
    inputEl.disabled = false;
    formEl.querySelector("button").disabled = false;
    addMessage(`<span class="error-text">No se pudo guardar la solicitud.</span><br>${formatErrors(result.errors)}`, "bot", true);
    return;
  }

  state.finished = true;
  addMessage(
    `La solicitud ha sido procesada y enviada al personal del CESFAM.<br><br>
    <strong>Nivel de Prioridad Asignado:</strong> ${result.priorizacion_solicitud}<br>
    <strong>ID de solicitud:</strong> ${result.id_solicitud}<br>
    <strong>Resumen de sintomas:</strong> ${escapeHtml(result.resumen.detalle_motivo)}
    <div class="summary-card">
      <strong>Que significa esta prioridad</strong>
      Tu consulta sera revisada por el equipo de salud. Los casos mas urgentes tienen precedencia segun disponibilidad y protocolo.
    </div>
    <br><strong>Importante:</strong> Recuerda que los cupos medicos son limitados.`,
    "bot",
    true
  );
  inputEl.placeholder = "La conversacion ha terminado.";
}

function formatErrors(errors) {
  if (Array.isArray(errors)) return errors.map(escapeHtml).join("<br>");
  return Object.entries(errors || {})
    .map(([field, values]) => `${escapeHtml(field)}: ${values.map(escapeHtml).join(", ")}`)
    .join("<br>");
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function getCookie(name) {
  const cookies = document.cookie.split(";").map((cookie) => cookie.trim());
  const target = cookies.find((cookie) => cookie.startsWith(`${name}=`));
  return target ? decodeURIComponent(target.split("=").slice(1).join("=")) : "";
}

formEl.addEventListener("submit", async (event) => {
  event.preventDefault();
  if (state.finished) return;

  const value = inputEl.value.trim();
  if (!value) return;

  const step = currentStep();
  const error = step.validate(value);
  addMessage(value, "user");
  inputEl.value = "";

  if (error) {
    addMessage(error);
    return;
  }

  state.data[step.field] = step.transform ? step.transform(value) : value;
  state.stepIndex += 1;

  if (state.stepIndex >= steps.length) {
    await submitSolicitud();
  } else {
    askCurrentStep();
  }
});

askCurrentStep();
