require("dotenv").config();
const express = require("express");
const mongoose = require("mongoose");
const path = require("path");

const authRoutes = require("./routes/auth");

const app = express();
app.use(express.json());

// MongoDB
mongoose
  .connect(process.env.MONGO_URI)
  .then(() => console.log("✅ MongoDB connected"))
  .catch(err => console.log("❌ Mongo error", err));

// auth routes
app.use("/auth", authRoutes);

// static files
app.use("/static", express.static(path.join(__dirname, "../static")));

// pages
app.get("/", (req, res) => {
  res.sendFile(path.join(__dirname, "../templates", "admin_login.html"));
});

app.get("/login", (req, res) => {
  res.sendFile(path.join(__dirname, "../templates", "admin_login.html"));
});

app.get("/dashboard", (req, res) => {
  res.sendFile(path.join(__dirname, "../templates", "admin_dashboard.html"));
});


// server
require("dotenv").config();
const express = require("express");
const mongoose = require("mongoose");
const path = require("path");

const authRoutes = require("./routes/auth");

const app = express();
app.use(express.json());

// MongoDB
mongoose
  .connect(process.env.MONGO_URI)
  .then(() => console.log("✅ MongoDB connected"))
  .catch(err => console.log("❌ Mongo error", err));

// auth routes
app.use("/auth", authRoutes);

// static files
app.use("/static", express.static(path.join(__dirname, "../static")));

// pages
app.get("/", (req, res) => {
  res.sendFile(path.join(__dirname, "../templates", "admin_login.html"));
});

app.get("/login", (req, res) => {
  res.sendFile(path.join(__dirname, "../templates", "admin_login.html"));
});

app.get("/dashboard", (req, res) => {
  res.sendFile(path.join(__dirname, "../templates", "admin_dashboard.html"));
});


// server
const PORT = process.env.PORT || 3000;

app.listen(PORT, () => {
  console.log(`🚀 Server running on port ${PORT}`);
});
