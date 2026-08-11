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

const defaultAssistantText =
  "Hey👋, Feel free to ask me about my skills, experience, projects, availability, and more. I’ll answer based on my resume and profile.";

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

    const data = await response.json();

    if (!response.ok || !data.success) {
      const errorMessage = data?.message || data?.detail || "Unable to get a response from the backend.";
      placeholder.textContent = `Error: ${errorMessage}`;
      scrollChatToBottom();
      return;
    }

    placeholder.textContent = data.answer || "No answer returned.";
    scrollChatToBottom();
    renderStatus("Chat response received.");
  } catch (error) {
    placeholder.textContent = `Error: ${error.message}`;
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

window.addEventListener("click", (event) => {
  if (
    settingsDrawer.classList.contains("visible") &&
    !settingsDrawer.contains(event.target) &&
    event.target !== settingsToggle
  ) {
    closeSettings();
  }
});

window.addEventListener("load", () => {
  renderMessage(defaultAssistantText, "assistant");
});
