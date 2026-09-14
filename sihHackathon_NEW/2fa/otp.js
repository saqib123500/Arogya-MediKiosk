const express = require("express");
const bodyParser = require("body-parser");
const JsonDB = require("node-json-db").JsonDB;
const Config = require("node-json-db/dist/lib/JsonDBConfig").Config;
const uuid = require("uuid");
const speakeasy = require("speakeasy");
const bcrypt = require("bcrypt");

const app = express();

const dbConfig = new Config(
  "myDataBase",
  true,
  false,
  "/"
);

const db = new JsonDB(dbConfig);

app.use(bodyParser.json());
app.use(bodyParser.urlencoded({ extended: true }));

// Health check
app.get("/api", (req, res) => {
  res.json({
    message: "Welcome to the two factor authentication example"
  });
});


// ==========================================
// REGISTER / GENERATE OTP
// ==========================================
app.post("/api/register", async (req, res) => {
  const { abhaId } = req.body;

  if (!abhaId) {
    return res.status(400).json({
      error: "ABHA ID is required."
    });
  }

  // Demo mapping: ABHA ID -> registered phone number
  const linkedPhones = {
    "12-3456-7890-1234": "+911234567890"
  };

  const phone = linkedPhones[abhaId];

  if (!phone) {
    return res.status(404).json({
      error: "ABHA ID not found."
    });
  }

  // Generate TOTP secret
  const secret = speakeasy.generateSecret({
    length: 20
  });

  const userId = uuid.v4();

  // Generate 6-digit OTP valid for 5 minutes
  const otp = speakeasy.totp({
    secret: secret.base32,
    encoding: "base32",
    step: 300
  });

  // Hash OTP before storing it
  const otpHash = await bcrypt.hash(String(otp), 10);

  // OTP expires after 5 minutes
  const otpExpiresAt = new Date(
    Date.now() + 5 * 60 * 1000
  ).toISOString();

  // Store user and OTP information in database
  db.push(`/users/${userId}`, {
    userId,
    abhaId,
    phone,
    otpHash,
    otpExpiresAt,
    secret: secret.base32,
    verified: false,
    createdAt: new Date().toISOString()
  });

  // OTP Simulator
  console.log("\n========== OTP SIMULATOR ==========");
  console.log(`Sending OTP to: ${phone}`);
  console.log(`Your OTP is: ${otp}`);
  console.log("===================================\n");

  console.log(
    `[REGISTER] ABHA=${abhaId} phone=${phone} OTP=${otp}`
  );

  // Response for development/testing
  res.status(201).json({
    message: "OTP generated successfully.",
    userId,
    abhaId,
    phone,
    otp
  });
});


// ==========================================
// VERIFY OTP
// ==========================================

app.post("/api/verify-otp", async (req, res) => {

  const { userId, otp } = req.body;

  if (!userId || !otp) {
    return res.status(400).json({
      error: "userId and otp are required."
    });
  }

  let user;

  try {
    user = await db.getData(`/users/${userId}`);
  } catch (e) {
    return res.status(404).json({
      error: "User not found. Please register first."
    });
  }

  // Check OTP expiry
  if (
    !user.otpExpiresAt ||
    new Date() > new Date(user.otpExpiresAt)
  ) {
    return res.status(401).json({
      success: false,
      message: "OTP has expired."
    });
  }

  // Compare entered OTP with stored hash
  const isValid = await bcrypt.compare(
    String(otp),
    user.otpHash
  );

  if (!isValid) {
    return res.status(401).json({
      success: false,
      message: "Invalid OTP."
    });
  }

  // Mark patient as verified
  db.push(
    `/users/${userId}/verified`,
    true
  );

  // Invalidate OTP after successful verification
  db.push(
    `/users/${userId}/otpHash`,
    null
  );

  db.push(
    `/users/${userId}/otpExpiresAt`,
    null
  );

  console.log(
    `[VERIFY] userId=${userId} — OTP verified successfully.`
  );

  res.json({
    success: true,
    message: "OTP verified successfully! User is now authenticated."
  });
});


// ==========================================
// START SERVER
// ==========================================

const port = 9000;

app.listen(port, () => {
  console.log(
    `App is running on PORT: ${port}.`
  );
});
