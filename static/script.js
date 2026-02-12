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
let username = localStorage.getItem("username");

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

/* ================= MOBILE SIDEBAR ================= */
if (mobileMenu) {
  mobileMenu.addEventListener("click", e => {
    e.stopPropagation();
    sidebar.classList.toggle("open");
  });
}

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

/* ================= INLINE MENU ================= */
function closeAllMenus() {
  document.querySelectorAll(".inline-menu").forEach(menu => {
    menu.style.display = "none";
  });
}

document.addEventListener("click", e => {
  if (!e.target.closest(".more-btn") && !e.target.closest(".inline-menu")) {
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
    menu.style.left = rect.right - menuWidth + "px";
  } else {
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
      sidebar.classList.remove("open");
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
  if (!text || !username) return;

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
      username: username
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

/* ================= LOGIN / REGISTER SYSTEM ================= */

const loginPage = document.getElementById("loginPage");
const chatApp = document.getElementById("chatApp");
const loginBtn = document.getElementById("loginBtn");
const loginUsername = document.getElementById("loginUsername");
const loginPassword = document.getElementById("loginPassword");
const togglePassword = document.getElementById("togglePassword");
const loginError = document.getElementById("loginError");
const switchModeBtn = document.getElementById("switchMode");
const loginTitle = document.getElementById("loginTitle");
const switchText = document.getElementById("switchText");

let isRegisterMode = false;

// Hide chat app initially
chatApp.style.display = "none";

// Auto login
if (username) {
  loginPage.style.display = "none";
  chatApp.style.display = "flex";
}

switchModeBtn.addEventListener("click", () => {
  isRegisterMode = !isRegisterMode;
  loginError.textContent = "";

  if (isRegisterMode) {
    loginTitle.textContent = "Create Account";
    loginBtn.textContent = "Register";
    switchText.textContent = "Already have an account?";
    switchModeBtn.textContent = "Login";
  } else {
    loginTitle.textContent = "Login";
    loginBtn.textContent = "Login";
    switchText.textContent = "New here?";
    switchModeBtn.textContent = "Create account";
  }
});

loginBtn.addEventListener("click", async () => {
  const u = loginUsername.value.trim();
  const p = loginPassword.value.trim();

  loginError.textContent = "";

  if (!u || !p) {
    loginError.textContent = "Username and password required";
    return;
  }

  const url = isRegisterMode ? "/register" : "/login";

  try {
    const res = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username: u, password: p })
    });

    const data = await res.json();

    if (data.success) {
      if (isRegisterMode) {
        loginError.style.color = "#4caf50";
        loginError.textContent = "Account created. Please login.";
        isRegisterMode = false;
        loginTitle.textContent = "Login";
        loginBtn.textContent = "Login";
        switchText.textContent = "New here?";
        switchModeBtn.textContent = "Create account";
      } else {
        localStorage.setItem("username", data.username);
        username = data.username;
        loginPage.style.display = "none";
        chatApp.style.display = "flex";
      }
    } else {
      loginError.style.color = "#ff4d4d";
      loginError.textContent = data.message || "Invalid username or password";
    }
  } catch (err) {
    console.error("Auth error:", err);
    loginError.textContent = "Server error. Try again.";
  }
});

/* Password Toggle */
if (togglePassword) {
  togglePassword.addEventListener("click", () => {
    loginPassword.type =
      loginPassword.type === "password" ? "text" : "password";
  });
}



/* ================= INIT ================= */
