(async function () {
  const out = document.getElementById('out');
  const status = document.getElementById('status');
  const roomInfo = document.getElementById('room-info');
  const roomIdSpan = document.getElementById('room-id');
  const listenerCountSpan = document.getElementById('listener-count');
  const profile = document.getElementById('profile');
  const avatarImg = document.getElementById('avatar');
  const usernameSpan = document.getElementById('username');

  function show(v) {
    out.textContent = JSON.stringify(v, null, 2);
  }

  const tg = window.Telegram?.WebApp || null;
  if (!tg) {
    status.textContent = "❌ Telegram WebApp not available; open inside Telegram.";
    return;
  }

  tg.ready();

  const unsafe = tg.initDataUnsafe || null;
  const signed = tg.initData || null;

  function hasHash(s) {
    return s && s.includes("hash=");
  }

  // Show initial debug values
  show({ ua: navigator.userAgent, hasWebApp: !!tg, initDataUnsafe: unsafe, initData: signed });

  if (!hasHash(signed)) {
    status.textContent = "⚠️ Verification data missing.\nPlease open this WebApp by tapping the bot's WebApp button inside Telegram.";
    return;
  }

  status.textContent = "Sending data to server for verification...";

  try {
    const r = await fetch('/verify_init', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ initData: signed, initDataUnsafe: unsafe })
    });
    const js = await r.json();
    show(js);

    if (js.ok) {
      status.textContent = "✅ Verified";
      status.style.color = "#4a90e2"; // Green for success

      if (js.room_id) {
        roomIdSpan.textContent = `Room - ${js.room_id}`;
        listenerCountSpan.textContent = `${js.listener_count} listener${js.listener_count > 1 ? 's' : ''}`;
        roomInfo.style.display = 'block';
      }

      if (unsafe?.user) {
        const user = unsafe.user;
        usernameSpan.textContent = user.username || user.first_name || 'Anonymous';
        profile.style.display = 'flex';
        if (user.photo_url) {
          avatarImg.src = user.photo_url;
        } else if (js.profile_photo_url) {
          avatarImg.src = js.profile_photo_url;
        } else {
          avatarImg.src = "/static/default-avatar.png";
        }
      }
    } else {
      status.textContent = `❌ Verification failed: ${js.error || 'Unknown error'}`;
      status.style.color = "#ff4444"; // Red for error
    }
  } catch (e) {
    status.textContent = "Network error: " + e.message;
    status.style.color = "#ff4444";
    show({ error: e.message });
  }

  // Send debug info silently
  fetch('/debug_client', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      ua: navigator.userAgent,
      initDataUnsafe: unsafe,
      initDataSigned: !!signed
    })
  }).catch(() => {});
})();
