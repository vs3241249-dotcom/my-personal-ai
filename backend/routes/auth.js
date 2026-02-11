const express = require("express");
const router = express.Router();
const User = require("../models/User");
const bcrypt = require("bcryptjs");

/* REGISTER */
router.post("/register", async (req, res) => {
  const { username, email, password } = req.body;

  if (!username || !email || !password) {
    return res.json({ success: false, message: "All fields required" });
  }

  const existing = await User.findOne({ username });
  if (existing) {
    return res.json({ success: false, message: "User already exists" });
  }

  const hashed = await bcrypt.hash(password, 10);

  const newUser = new User({
    username,
    email,
    password: hashed
  });

  await newUser.save();

  res.json({ success: true, message: "Registered successfully" });
});

/* LOGIN */
router.post("/login", async (req, res) => {
  const { username, password } = req.body;

  const user = await User.findOne({ username });
  if (!user) {
    return res.json({ success: false, message: "User not found" });
  }

  const match = await bcrypt.compare(password, user.password);
  if (!match) {
    return res.json({ success: false, message: "Wrong password" });
  }

  res.json({ success: true, username: user.username });
});

module.exports = router;
