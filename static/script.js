 const chatDiv = document.getElementById("chat");
const input = document.getElementById("input");
const sendBtn = document.getElementById("send");
const historyDiv = document.getElementById("history");
const newChatBtn = document.getElementById("newChat");
const themeToggle = document.getElementById("themeToggle");
const mobileMenu = document.getElementById("mobileMenu");
const sidebar = document.getElementById("sidebar");
const body = document.body;

/* ================= USER ================= */
const username = localStorage.getItem("username") || "Guest";

/* ================= STORAGE ================= */
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

/* ================= MOBILE SIDEBAR (☰) ================= */
if (mobileMenu) {
  mobileMenu.addEventListener("click", e => {
    e.stopPropagation();
    sidebar.classList.toggle("open");
  });
}

/* Outside click → close sidebar (MOBILE ONLY) */
document.addEventListener("click", e => {
  if (
    sidebar.classList.contains("open") &&
    !sidebar.contains(e.target) &&
    !mobileMenu.contains(e.target)
  ) {
    sidebar.classList.remove("open");
  }
});

/* ================= SAVE ================= */
function saveChats() {
  localStorage.setItem("chats", JSON.stringify(chats));
}

/* ================= INLINE MENU (3 DOT) ================= */
function closeAllMenus() {
  document.querySelectorAll(".inline-menu").forEach(menu => {
    menu.style.display = "none";
  });
}

/* ❗ IMPORTANT: mobile-friendly close logic */
document.addEventListener("click", e => {
  if (
    !e.target.closest(".more-btn") &&
    !e.target.closest(".inline-menu")
  ) {
    closeAllMenus();
  }
});

function createMenu(onCopy, onDelete) {
  const menu = document.createElement("div");
  menu.className = "inline-menu";
  menu.style.display = "none";
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

  const rect = btn.getBoundingClientRect();
  const menuWidth = 140;
  const screenWidth = window.innerWidth;

  menu.style.display = "block";
  menu.style.position = "fixed";
  menu.style.top = rect.bottom + "px";

  if (rect.right + menuWidth > screenWidth) {
    /* USER MESSAGE (right side) */
    menu.style.left = rect.right - menuWidth + "px";
  } else {
    /* BOT MESSAGE (left side) */
    menu.style.left = rect.left + "px";
  }

  menu.style.right = "auto";
}


/* ================= CHAT HISTORY ================= */
function renderHistory() {
  historyDiv.innerHTML = "";

  chats.forEach((c, i) => {
    const row = document.createElement("div");
    row.className = "chat-title" + (i === currentChatIndex ? " active" : "");
    row.textContent = `Chat ${i + 1}`;

    row.onclick = () => {
      currentChatIndex = i;
      renderChat();
      renderHistory();
      sidebar.classList.remove("open"); // mobile auto close
    };

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

/* ================= SEND MESSAGE ================= */
function sendMessage() {
  const text = input.value.trim();
  if (!text) return;

  if (currentChatIndex === null) {
    chats.push({ messages: [] });
    currentChatIndex = chats.length - 1;
  }

  chats[currentChatIndex].messages.push({ role: "user", text });
  input.value = "";
  autoResize();
  saveChats();
  renderChat();
  renderHistory();

  const typing = document.createElement("div");
  typing.className = "msg bot";
  typing.textContent = "AI is typing...";
  chatDiv.appendChild(typing);

  fetch("/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      message: text,
      username: username // 🔒 admin safe
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
/* ================= LOGIN AUTH LOGIC ================= */

const loginPage = document.getElementById("loginPage");
const chatApp = document.getElementById("chatApp");
const loginBtn = document.getElementById("loginBtn");
const loginUsername = document.getElementById("loginUsername");
const loginPassword = document.getElementById("loginPassword");

/* Hide chatbot first */
chatApp.style.display = "none";

/* Get saved credentials */
const savedUser = localStorage.getItem("auth_user");
const savedPass = localStorage.getItem("auth_pass");

/* Auto login only if credentials exist */
if (savedUser && savedPass) {
  loginPage.style.display = "none";
  chatApp.style.display = "flex";
}

/* Login click */
loginBtn.addEventListener("click", () => {
  const u = loginUsername.value.trim();
  const p = loginPassword.value.trim();

  if (!u || !p) {
    alert("Username & password required");
    return;
  }

  /* FIRST TIME REGISTER */
  if (!savedUser || !savedPass) {
    localStorage.setItem("auth_user", u);
    localStorage.setItem("auth_pass", p);
    localStorage.setItem("username", u); // chatbot ke liye

    loginPage.style.display = "none";
    chatApp.style.display = "flex";
    return;
  }

  /* NORMAL LOGIN */
  if (u === savedUser && p === savedPass) {
    localStorage.setItem("username", u);
    loginPage.style.display = "none";
    chatApp.style.display = "flex";
  } else {
    alert("❌ Wrong username or password");
  }
});
