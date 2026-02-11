require("dotenv").config();
const express = require("express");
const mongoose = require("mongoose");
const path = require("path");
const cors = require("cors");

const authRoutes = require("./routes/auth");

const app = express();

/* ================= MIDDLEWARE ================= */
app.use(cors());
app.use(express.json());

/* ================= MONGODB ================= */
mongoose
  .connect(process.env.MONGO_URI)
  .then(() => console.log("✅ MongoDB connected"))
  .catch(err => console.log("❌ Mongo error", err));

/* ================= ROUTES ================= */
app.use("/auth", authRoutes);

/* ================= STATIC FILES ================= */
app.use("/static", express.static(path.join(__dirname, "../static")));

/* ================= PAGES ================= */
app.get("/", (req, res) => {
  res.sendFile(path.join(__dirname, "../templates", "admin_login.html"));
});

app.get("/login", (req, res) => {
  res.sendFile(path.join(__dirname, "../templates", "admin_login.html"));
});

app.get("/dashboard", (req, res) => {
  res.sendFile(path.join(__dirname, "../templates", "admin_dashboard.html"));
});

/* ================= SERVER ================= */
const PORT = process.env.PORT || 3000;

app.listen(PORT, () => {
  console.log(`🚀 Server running on port ${PORT}`);
});
