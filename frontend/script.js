const chatWindow = document.getElementById("chat-window");
const chatForm = document.getElementById("chat-form");
const messageInput = document.getElementById("message-input");
const backendUrlInput = document.getElementById("backend-url");
const uploadButton = document.getElementById("upload-button");
const resumeFileInput = document.getElementById("resume-file");
const uploadStatus = document.getElementById("upload-status");
const settingsToggle = document.getElementById("settings-toggle");
const settingsDrawer = document.getElementById("settings-drawer");
const settingsClose = document.getElementById("settings-close");
const themeToggle = document.getElementById("theme-toggle");
const themeModal = document.getElementById("theme-modal");
const themeClose = document.getElementById("theme-close");
const modeCards = [...document.querySelectorAll("[data-mode]")];
const themeCards = [...document.querySelectorAll("[data-theme]")];

const defaultAssistantText =
  "Hey👋, Feel free to ask me about my skills, experience, projects, availability, and more. I’ll answer based on my resume and profile.";
const STORAGE_KEY = "hireme_backend_url";
const DEFAULT_BACKEND_URL = "https://chatbot-hireme.onrender.com";
const LOCAL_BACKEND_URL = "http://127.0.0.1:8000";
const THEME_STORAGE_KEY = "hireme_theme_settings";
const themePalettes = {
  midnight: { bg: "#0a1120", panel: "#0e172c", surface: "#111c34", accent: "#38bdf8", strong: "#7dd3fc" },
  ocean: { bg: "#0a1a2d", panel: "#102746", surface: "#183258", accent: "#60a5fa", strong: "#bfdbfe" },
  onyx: { bg: "#151515", panel: "#222222", surface: "#2b2b2b", accent: "#d4d4d8", strong: "#fafafa" },
  ember: { bg: "#21150f", panel: "#3a2418", surface: "#4b2e1d", accent: "#fb923c", strong: "#fed7aa" },
  moss: { bg: "#172015", panel: "#25301d", surface: "#303e25", accent: "#d4c94a", strong: "#fef08a" },
};

function applyTheme(mode, theme) {
  const palette = themePalettes[theme] || themePalettes.midnight;
  document.body.dataset.mode = mode;
  document.body.dataset.theme = theme;
  document.documentElement.style.setProperty("--bg", palette.bg);
  document.documentElement.style.setProperty("--panel", palette.panel);
  document.documentElement.style.setProperty("--surface", palette.surface);
  document.documentElement.style.setProperty("--accent", palette.accent);
  document.documentElement.style.setProperty("--accent-strong", palette.strong);
  localStorage.setItem(THEME_STORAGE_KEY, JSON.stringify({ mode, theme }));
  modeCards.forEach((card) => card.classList.toggle("selected", card.dataset.mode === mode));
  themeCards.forEach((card) => card.classList.toggle("selected", card.dataset.theme === theme));
}

function loadTheme() {
  try {
    const saved = JSON.parse(localStorage.getItem(THEME_STORAGE_KEY) || "{}");
    applyTheme(saved.mode || "dark", saved.theme || "midnight");
  } catch {
    applyTheme("dark", "midnight");
  }
}

function openThemeManager() {
  themeModal.classList.add("visible");
  themeModal.setAttribute("aria-hidden", "false");
  themeToggle.setAttribute("aria-expanded", "true");
}

function closeThemeManager() {
  themeModal.classList.remove("visible");
  themeModal.setAttribute("aria-hidden", "true");
  themeToggle.setAttribute("aria-expanded", "false");
}

function getStoredBackendUrl() {
  return localStorage.getItem(STORAGE_KEY) || "";
}

function saveBackendUrl(url) {
  localStorage.setItem(STORAGE_KEY, url);
}


function getDefaultBackendUrl() {
  const savedUrl = getStoredBackendUrl();
  if (savedUrl) {
    return savedUrl;
  }


  
  const isLocalhost = window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1";
  const selectedUrl = isLocalhost ? LOCAL_BACKEND_URL : DEFAULT_BACKEND_URL;
  saveBackendUrl(selectedUrl);
  return selectedUrl;
}

function scrollChatToBottom() {
  requestAnimationFrame(() => {
    chatWindow.scrollTop = chatWindow.scrollHeight;
    const lastMessage = chatWindow.lastElementChild;
    if (lastMessage) {
      lastMessage.scrollIntoView({ block: "end", inline: "nearest" });
    }
  });
}

function renderMessage(text, sender) {
  const message = document.createElement("div");
  message.className = `message ${sender}`;

  const label = document.createElement("span");
  label.className = "label";
  label.textContent = sender === "user" ? "You" : "Assistant";

  const body = document.createElement("div");
  body.textContent = text;

  message.appendChild(label);
  message.appendChild(body);
  chatWindow.appendChild(message);
  scrollChatToBottom();
}

function renderStatus(text, isError = false) {
  uploadStatus.textContent = text;
  uploadStatus.style.color = isError ? "#fb7185" : "#94a3b8";
}

function formatUserFriendlyError(message) {
  const text = (message || "").toLowerCase();

  if (text.includes("rate limit") || text.includes("temporarily unavailable") || text.includes("try again in a couple of minutes")) {
    return "Something went wrong on the AI service. Please try again in a couple of minutes.";
  }

  if (text.includes("groq") || text.includes("api key") || text.includes("not configured")) {
    return "The assistant is not available right now. Please try again later.";
  }

  return "Something went wrong while generating the answer. Please try again in a moment.";
}

function applyBackendUrl(url) {
  const safeUrl = (url || "").trim();
  if (!safeUrl) {
    return;
  }

  backendUrlInput.value = safeUrl;
  backendUrlInput.disabled = true;
  saveBackendUrl(safeUrl);
}

async function sendChat(question) {
  const backendUrl = backendUrlInput.value.trim() || backendUrlInput.placeholder;
  if (!backendUrl) {
    renderStatus("Set the backend URL before sending a message.", true);
    return;
  }

  renderMessage(question, "user");
  renderMessage("Typing…", "assistant");
  const placeholder = chatWindow.querySelector(".message.assistant:last-child div");

  try {
    const response = await fetch(`${backendUrl}/api/chat`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ query: question }),
    });

    const rawText = await response.text();
    let data = {};

    if (rawText) {
      try {
        data = JSON.parse(rawText);
      } catch {
        data = { message: rawText };
      }
    }

    if (!response.ok || !data.success) {
      const errorMessage = data?.message || data?.detail || "Unable to get a response from the backend.";
      placeholder.textContent = formatUserFriendlyError(errorMessage);
      scrollChatToBottom();
      return;
    }

    placeholder.textContent = data.answer || "No answer returned.";
    scrollChatToBottom();
    renderStatus("Chat response received.");
  } catch (error) {
    placeholder.textContent = "Something went wrong while connecting to the assistant. Please try again in a moment.";
    renderStatus("Failed to call backend. Confirm the server is running.", true);
  }
}

async function uploadResume() {
  const file = resumeFileInput.files[0];
  if (!file) {
    renderStatus("Choose a PDF file first.", true);
    return;
  }

  const backendUrl = backendUrlInput.value.trim() || backendUrlInput.placeholder;
  if (!backendUrl) {
    renderStatus("Set the backend URL before uploading.", true);
    return;
  }

  const formData = new FormData();
  formData.append("file", file);

  uploadButton.disabled = true;
  uploadButton.textContent = "Uploading…";
  renderStatus("Indexing resume content...");

  try {
    const response = await fetch(`${backendUrl}/api/upload`, {
      method: "POST",
      body: formData,
    });

    const data = await response.json();
    if (!response.ok || !data.success) {
      renderStatus(data?.message || "Upload failed.", true);
      return;
    }

    renderStatus(`Indexed ${data.chunks} chunks from resume.`);
  } catch (error) {
    renderStatus(`Upload error: ${error.message}`, true);
  } finally {
    uploadButton.disabled = false;
    uploadButton.textContent = "Upload";
  }
}

function openSettings() {
  settingsDrawer.classList.add("visible");
  settingsDrawer.setAttribute("aria-hidden", "false");
  settingsToggle.setAttribute("aria-expanded", "true");
}

function closeSettings() {
  settingsDrawer.classList.remove("visible");
  settingsDrawer.setAttribute("aria-hidden", "true");
  settingsToggle.setAttribute("aria-expanded", "false");
}

chatForm.addEventListener("submit", (event) => {
  event.preventDefault();
  const question = messageInput.value.trim();
  if (!question) {
    return;
  }
  messageInput.value = "";
  sendChat(question);
});

uploadButton.addEventListener("click", uploadResume);
settingsToggle.addEventListener("click", openSettings);
settingsClose.addEventListener("click", closeSettings);
themeToggle.addEventListener("click", openThemeManager);
themeClose.addEventListener("click", closeThemeManager);
modeCards.forEach((card) => card.addEventListener("click", () => {
  const saved = JSON.parse(localStorage.getItem(THEME_STORAGE_KEY) || "{}");
  applyTheme(card.dataset.mode, saved.theme || "midnight");
}));
themeCards.forEach((card) => card.addEventListener("click", () => {
  const saved = JSON.parse(localStorage.getItem(THEME_STORAGE_KEY) || "{}");
  applyTheme(saved.mode || "dark", card.dataset.theme);
}));

backendUrlInput.addEventListener("keydown", (event) => {
  if (event.key === "Enter") {
    event.preventDefault();
    const enteredValue = backendUrlInput.value.trim();
    if (!enteredValue) {
      renderStatus("Enter a valid backend URL first.", true);
      return;
    }

    applyBackendUrl(enteredValue);
    renderStatus("Backend URL saved for this browser.");
    closeSettings();
  }
});

window.addEventListener("click", (event) => {
  if (
    settingsDrawer.classList.contains("visible") &&
    !settingsDrawer.contains(event.target) &&
    event.target !== settingsToggle
  ) {
    closeSettings();
  }

  if (themeModal.classList.contains("visible") && event.target === themeModal) {
    closeThemeManager();
  }
});

window.addEventListener("keydown", (event) => {
  if (event.key === "Escape") {
    closeThemeManager();
    closeSettings();
  }
});

window.addEventListener("load", () => {
  loadTheme();
  const defaultUrl = getDefaultBackendUrl();
  backendUrlInput.value = defaultUrl;
  backendUrlInput.disabled = true;

  renderMessage(defaultAssistantText, "assistant");
});
