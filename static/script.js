(async function () {
  const statusEl = document.getElementById("status");
  const avatarEl = document.getElementById("avatar");
  const nameEl = document.getElementById("name");
  const metaEl = document.getElementById("meta");
  const outEl = document.getElementById("out");

  function show(obj) {
    outEl.textContent = JSON.stringify(obj, null, 2);
  }

  const tg = window.Telegram?.WebApp;
  if (!tg) {
    statusEl.textContent = "❌ Open this inside Telegram Mini App.";
    return;
  }

  tg.ready();

  const initData = tg.initData || "";
  if (!initData.includes("hash=")) {
    statusEl.textContent = "⚠️ No initData found. Open from bot’s WebApp button.";
    return;
  }

  statusEl.textContent = "⏳ Verifying initData with server...";

  try {
    const res = await fetch("/verify_init", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ initData })
    });

    const js = await res.json();
    show(js);

    if (!js.ok) {
      statusEl.textContent = `❌ Verification failed: ${js.error}`;
      return;
    }

    statusEl.textContent = "✅ Verified";

    const u = js.user || {};
    const profileUrl = js.profile_photo_url || u.photo_url || "/static/default-avatar.png";

    avatarEl.src = profileUrl;
    nameEl.textContent = [u.first_name, u.last_name].filter(Boolean).join(" ") || "Unknown";
    metaEl.textContent = u.username ? `@${u.username}` : `id: ${u.id || "-"}`;

  } catch (err) {
    statusEl.textContent = "Network error: " + (err.message || err);
    show({ error: err.message || String(err) });
  }
})();
