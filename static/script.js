/* ================= ELEMENTS ================= */
const chatDiv = document.getElementById("chatBox");
const input = document.getElementById("messageInput");
const sendBtn = document.getElementById("send");
const historyDiv = document.getElementById("chatList");
const newChatBtn = document.getElementById("newChat");
const themeToggle = document.getElementById("themeToggle");
const menuBtn = document.getElementById("menuBtn");
const sidebar = document.getElementById("sidebar");
const userNameLabel = document.getElementById("userName");
const body = document.body;

/* ================= USER NAME ================= */
const savedName = localStorage.getItem("username");
if (savedName) {
  userNameLabel.textContent = savedName;
}

/* ================= SIDEBAR TOGGLE (MOBILE) ================= */
menuBtn.onclick = () => {
  sidebar.classList.toggle("open");
};

/* ================= DATA ================= */
let chats = JSON.parse(localStorage.getItem("chats")) || [];
let currentChatIndex = null;

/* ================= THEME ================= */
let theme = localStorage.getItem("theme") || "light";
body.className = theme;
themeToggle.textContent = theme === "dark" ? "🌙" : "🌞";

themeToggle.onclick = () => {
  theme = theme === "dark" ? "light" : "dark";
  body.className = theme;
  themeToggle.textContent = theme === "dark" ? "🌙" : "🌞";
  localStorage.setItem("theme", theme);
};

/* ================= SAVE ================= */
function saveChats() {
  localStorage.setItem("chats", JSON.stringify(chats));
}

/* ================= MENU HELPERS ================= */
function closeAllMenus() {
  document.querySelectorAll(".inline-menu").forEach(m => {
    m.style.display = "none";
  });
}
document.addEventListener("click", closeAllMenus);

function createMenu(onCopy, onDelete) {
  const menu = document.createElement("div");
  menu.className = "inline-menu";
  menu.innerHTML = `
    <div class="menu-item">📋 Copy</div>
    <div class="menu-item">🗑 Delete</div>
  `;

  menu.children[0].onclick = e => {
    e.stopPropagation();
    onCopy();
    menu.style.display = "none";
  };

  menu.children[1].onclick = e => {
    e.stopPropagation();
    onDelete();
    menu.style.display = "none";
  };

  return menu;
}

function toggleMenu(menu, btn) {
  closeAllMenus();
  menu.style.display = "block";
  menu.style.top = btn.offsetTop + btn.offsetHeight + "px";
  menu.style.left = btn.offsetLeft + "px";
}

/* ================= HISTORY ================= */
function renderHistory() {
  historyDiv.innerHTML = "";

  chats.forEach((c, i) => {
    const row = document.createElement("div");
    row.className = "chat-title" + (i === currentChatIndex ? " active" : "");
    row.textContent = c.title || `Chat ${i + 1}`;

    const moreBtn = document.createElement("button");
    moreBtn.className = "more-btn";
    moreBtn.textContent = "⋮";

    const menu = createMenu(
      () => navigator.clipboard.writeText(c.title),
      () => {
        chats.splice(i, 1);
        if (currentChatIndex === i) {
          currentChatIndex = null;
          chatDiv.innerHTML = "";
        }
        saveChats();
        renderHistory();
      }
    );

    moreBtn.onclick = e => {
      e.stopPropagation();
      toggleMenu(menu, moreBtn);
    };

    row.onclick = e => {
      if (e.target.classList.contains("more-btn")) return;
      currentChatIndex = i;
      renderChat();
      renderHistory();
      sidebar.classList.remove("open");
    };

    row.appendChild(moreBtn);
    row.appendChild(menu);
    historyDiv.appendChild(row);
  });
}

/* ================= CHAT ================= */
function renderChat() {
  chatDiv.innerHTML = "";
  if (currentChatIndex === null) return;

  chats[currentChatIndex].messages.forEach((m, idx) => {
    const msg = document.createElement("div");
    msg.className = "msg " + m.role;

    const text = document.createElement("span");
    text.textContent = m.text;

    const moreBtn = document.createElement("button");
    moreBtn.className = "more-btn";
    moreBtn.textContent = "⋮";

    const menu = createMenu(
      () => navigator.clipboard.writeText(m.text),
      () => {
        chats[currentChatIndex].messages.splice(idx, 1);
        saveChats();
        renderChat();
      }
    );

    moreBtn.onclick = e => {
      e.stopPropagation();
      toggleMenu(menu, moreBtn);
    };

    msg.appendChild(text);
    msg.appendChild(moreBtn);
    msg.appendChild(menu);
    chatDiv.appendChild(msg);
  });

  chatDiv.scrollTop = chatDiv.scrollHeight;
}

/* ================= NEW CHAT ================= */
newChatBtn.onclick = () => {
  currentChatIndex = null;
  chatDiv.innerHTML = "";
};

/* ================= INPUT ================= */
function autoResize() {
  input.style.height = "auto";
  input.style.height = input.scrollHeight + "px";
}
input.addEventListener("input", autoResize);

sendBtn.onclick = sendMessage;
input.addEventListener("keydown", e => {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    sendMessage();
  }
});

/* ================= SEND ================= */
function sendMessage() {
  const text = input.value.trim();
  if (!text) return;

  if (currentChatIndex === null) {
    chats.push({ title: text.slice(0, 30), messages: [] });
    currentChatIndex = chats.length - 1;
  }

  chats[currentChatIndex].messages.push({ role: "user", text });
  input.value = "";
  autoResize();
  saveChats();
  renderChat();
  renderHistory();

  const typing = document.createElement("div");
  typing.className = "msg bot typing";
  typing.textContent = "AI is typing...";
  chatDiv.appendChild(typing);

  fetch("/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      message: text,
      name: localStorage.getItem("username") || "Guest"
    })
  })
    .then(res => res.json())
    .then(data => {
      typing.remove();
      chats[currentChatIndex].messages.push({
        role: "bot",
        text: data.reply
      });
      saveChats();
      renderChat();
    });
}

/* ================= INIT ================= */
renderHistory();
