const mongoose = require("mongoose");

const PasswordResetSchema = new mongoose.Schema({
  email: {
    type: String,
    required: true
  },
  token: {
    type: String,
    required: true
  },
  expiresAt: {
    type: Date,
    required: true,
    index: { expires: 0 } // Mongo auto delete
  }
});

module.exports = mongoose.model("PasswordReset", PasswordResetSchema);
