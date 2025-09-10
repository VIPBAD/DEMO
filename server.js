import express from "express";
import crypto from "crypto";
import bodyParser from "body-parser";
import path from "path";
import dotenv from "dotenv";

dotenv.config();

const BOT_TOKEN = process.env.BOT_TOKEN;
if (!BOT_TOKEN) {
  throw new Error("BOT_TOKEN not set in environment");
}

const app = express();
app.use(bodyParser.json());

// Serve static and templates
const __dirname = path.resolve();
app.use("/static", express.static(path.join(__dirname, "static")));

// Make secret key (per Telegram spec)
function makeSecretKey(botToken: string): Buffer {
  return crypto.createHmac("sha256", "WebAppData")
    .update(botToken)
    .digest();
}

// Verify initData
function verifyInitData(initData: string): Record<string, string> {
  if (!initData || !initData.includes("hash=")) {
    throw new Error("init_data missing or invalid");
  }

  const parts = initData.split("&");
  const data: Record<string, string> = {};
  let hashValue: string | null = null;

  for (const p of parts) {
    const [k, v] = p.split("=", 2);
    if (k === "hash") {
      hashValue = v;
    } else if (k) {
      data[k] = v;
    }
  }

  if (!hashValue) {
    throw new Error("hash not found in init_data");
  }

  // Create data_check_string
  const items = Object.entries(data)
    .map(([k, v]) => `${k}=${v}`)
    .sort();
  const dataCheckString = items.join("\n");

  const secretKey = makeSecretKey(BOT_TOKEN!);
  const computedHash = crypto
    .createHmac("sha256", secretKey)
    .update(dataCheckString)
    .digest("hex");

  if (computedHash !== hashValue) {
    throw new Error("init_data verification failed");
  }

  return data;
}

// API endpoint
app.post("/verify_init", (req, res) => {
  const { initData } = req.body;
  if (!initData) {
    return res.status(400).json({ ok: false, error: "initData missing" });
  }

  try {
    const parsed = verifyInitData(initData);
    return res.json({ ok: true, verified: true, data: parsed });
  } catch (err: any) {
    console.error("❌ VERIFY FAILED:", err.message);
    return res.status(403).json({ ok: false, error: err.message });
  }
});

// Serve index.html
app.get("/", (req, res) => {
  res.sendFile(path.join(__dirname, "templates/index.html"));
});

// Start server
const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
  console.log(`🚀 Server running on http://localhost:${PORT}`);
});
