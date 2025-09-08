(async function () {
  const out = document.getElementById('out');
  const status = document.getElementById('status');
  const profileCard = document.getElementById('profile-card');
  const avatar = document.getElementById('avatar');
  const username = document.getElementById('username');
  const favorites = document.getElementById('favorites');
  const totalPlays = document.getElementById('total-plays');

  function show(v) {
    out.textContent = JSON.stringify(v, null, 2);
  }

  const tg = window.Telegram?.WebApp || null;
  if (!tg) {
    status.textContent = "❌ Telegram WebApp not available; open inside Telegram.";
    return;
  }

  tg.ready();

  const signed = tg.initData || null;

  function hasHash(s) {
    return s && s.includes("hash=");
  }

  if (!hasHash(signed)) {
    status.textContent = "⚠️ Verification data missing.\nPlease open this WebApp by tapping the bot's WebApp button inside Telegram.";
    return;
  }

  status.textContent = "Sending data to server for verification...";

  try {
    const r = await fetch('/verify_init', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ initData: signed })
    });
    const js = await r.json();
    show(js);

    if (js.ok) {
      status.textContent = "✅ Verified";
      status.className = "success";

      profileCard.style.display = 'block';
      if (js.user) {
        // Custom username with emojis
        const customName = `("${js.user.first_name || 'User'} [🌸] '♥_♥'")`;
        username.textContent = customName;
        favorites.textContent = "0"; // Hardcoded for now; can be dynamic if stored
        totalPlays.textContent = "1"; // Hardcoded for now; can be dynamic if stored
        if (js.profile_photo_url) {
          avatar.src = js.profile_photo_url;
        } else if (js.user.photo_url) {
          avatar.src = js.user.photo_url;
        }
      }
    } else {
      status.textContent = `❌ Verification failed: ${js.error || 'Unknown error'}`;
    }
  } catch (e) {
    status.textContent = "Network error: " + e.message;
    show({ error: e.message });
  }
})();
