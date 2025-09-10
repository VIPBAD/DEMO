// static/script.js
(async function () {
  const statusEl = document.getElementById("status");
  const out = document.getElementById("out");
  const avatar = document.getElementById("avatar");
  const nameEl = document.getElementById("name");
  const metaEl = document.getElementById("meta");

  function show(obj) {
    out.textContent = JSON.stringify(obj, null, 2);
  }

  const tg = window.Telegram?.WebApp ?? null;
  if (!tg) {
    statusEl.textContent = "❌ Open this inside Telegram (Mini App).";
    return;
  }

  tg.ready();

  // initData is a query-string-like string provided when opened from Telegram
  const initData = tg.initData ?? null;
  if (!initData || !initData.includes("hash=")) {
    statusEl.textContent = "⚠️ initData/hash missing. Launch the WebApp from Telegram.";
    return;
  }

  statusEl.textContent = "Sending initData to server for verification...";

  try {
    const res = await fetch("/verify_init", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ initData })
    });
    const js = await res.json();
    show(js);

    if (!js.ok) {
      statusEl.textContent = `❌ Verification failed: ${js.error ?? "unknown"}`;
      return;
    }

    statusEl.textContent = "✅ Verified";

    // Present user info
    const u = js.user ?? null;
    const profile_photo_url = js.profile_photo_url ?? (u ? u.photo_url : null);

    if (u && u.first_name) {
      const parts = [];
      parts.push(u.first_name || "");
      if (u.last_name) parts.push(u.last_name);
      nameEl.textContent = parts.join(" ");
      metaEl.textContent = u.username ? `@${u.username}` : `id: ${u.id}`;
    } else {
      nameEl.textContent = "User";
      metaEl.textContent = `id: ${u?.id ?? "unknown"}`;
    }

    if (profile_photo_url) {
      avatar.src = profile_photo_url;
    } else {
      avatar.src = "/static/default-avatar.png";
    }

  } catch (err) {
    statusEl.textContent = "Network error: " + (err.message || err);
    show({ error: err.message ?? String(err) });
  }
})();
