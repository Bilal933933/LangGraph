// عميل الواجهة: يرسل الرسالة إلى POST /chat ويعرض الرد.

const API_BASE = "http://127.0.0.1:8000";

const form = document.getElementById("chat-form");
const input = document.getElementById("message-input");
const sendButton = document.getElementById("send-button");
const messagesBox = document.getElementById("messages");
const statusLine = document.getElementById("status");

function addMessage(text, kind) {
  const div = document.createElement("div");
  div.className = "message " + kind;
  div.textContent = text;
  messagesBox.appendChild(div);
  messagesBox.scrollTop = messagesBox.scrollHeight;
}

async function sendMessage(text) {
  const response = await fetch(API_BASE + "/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message: text }),
  });
  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.detail || ("خطأ " + response.status));
  }
  return data.reply;
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const text = input.value.trim();
  if (!text) {
    return;
  }
  addMessage(text, "user");
  input.value = "";
  sendButton.disabled = true;
  statusLine.textContent = "جارٍ التفكير…";

  try {
    const reply = await sendMessage(text);
    addMessage(reply, "assistant");
    statusLine.textContent = "";
  } catch (error) {
    addMessage(String(error.message || error), "error");
    statusLine.textContent = "تأكد أن السيرفر يعمل وأن GOOGLE_API_KEY مضبوط.";
  } finally {
    sendButton.disabled = false;
  }
});
