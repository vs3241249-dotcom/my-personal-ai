const express = require("express");
const bcrypt = require("bcrypt");
const crypto = require("crypto");

const User = require("../models/User");
const PasswordReset = require("../models/PasswordReset");
const sendEmail = require("../utils/sendEmail");

const router = express.Router();

/* SIGNUP */
router.post("/signup", async (req, res) => {
  const { email, password } = req.body;

  if (!email || !password)
    return res.status(400).json({ error: "Missing fields" });

  const existing = await User.findOne({ email });
  if (existing)
    return res.status(400).json({ error: "User already exists" });

  const hashed = await bcrypt.hash(password, 10);
  await User.create({ email, password: hashed });

  res.json({ success: true });
});

/* LOGIN */
router.post("/login", async (req, res) => {
  const { email, password } = req.body;

  const user = await User.findOne({ email });
  if (!user)
    return res.status(401).json({ error: "Invalid credentials" });

  const match = await bcrypt.compare(password, user.password);
  if (!match)
    return res.status(401).json({ error: "Invalid credentials" });

  user.lastLogin = new Date();
  await user.save();

  res.json({ success: true });
});

/* FORGOT PASSWORD */
router.post("/forgot-password", async (req, res) => {
  const { email } = req.body;

  const user = await User.findOne({ email });
  if (!user) return res.json({ success: true });

  const token = crypto.randomBytes(32).toString("hex");

  await PasswordReset.create({
    email,
    token,
    expiresAt: Date.now() + 15 * 60 * 1000
  });

  const link = `http://localhost:3000/reset-password?token=${token}`;

  await sendEmail(
    email,
    "Reset Password",
    `<p>Click to reset password:</p><a href="${link}">${link}</a>`
  );

  res.json({ success: true });
});

/* RESET PASSWORD */
router.post("/reset-password", async (req, res) => {
  const { token, newPassword } = req.body;

  const record = await PasswordReset.findOne({ token });
  if (!record || record.expiresAt < Date.now())
    return res.status(400).json({ error: "Token expired" });

  const hashed = await bcrypt.hash(newPassword, 10);

  await User.updateOne(
    { email: record.email },
    { password: hashed }
  );

  await PasswordReset.deleteOne({ token });

  res.json({ success: true });
});

module.exports = router;
router.post("/signup", async (req, res) => {
  try {
    const { email, password } = req.body;
    if (!email || !password)
      return res.status(400).json({ error: "Missing fields" });

    const existing = await User.findOne({ email });
    if (existing)
      return res.status(400).json({ error: "User already exists" });

    const hashed = await bcrypt.hash(password, 10);
    await User.create({ email, password: hashed });

    res.json({ success: true });
  } catch (err) {
    res.status(500).json({ error: "Server error" });
  }
});

