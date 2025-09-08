(async function(){
  const out = document.getElementById('out');
  const status = document.getElementById('status');
  const roomInfo = document.getElementById('room-info');
  const roomIdSpan = document.getElementById('room-id');
  const listenerCountSpan = document.getElementById('listener-count');
  const profile = document.getElementById('profile');
  const avatarImg = document.getElementById('avatar');
  const usernameSpan = document.getElementById('username');

  function show(v){ out.textContent = JSON.stringify(v, null, 2); }

  const tg = window.Telegram?.WebApp || null;
  if (!tg) {
    status.textContent = "Telegram WebApp not available; open inside Telegram.";
    return;
  }

  tg.ready();  // Initialize WebApp

  const unsafe = tg.initDataUnsafe || null;
  const signed = tg.initData || null;

  // Show initial client-side data
  show({ ua: navigator.userAgent, hasWebApp: !!tg, initDataUnsafe: unsafe ? unsafe : null, initData: signed ? signed : null });
  status.textContent = "collected client values — sending to server for verification...";

  if (signed) {
    try {
      // Fetch data from server
      const r = await fetch('/verify_init', {
        method: 'POST',
        headers: {'Content-Type':'application/json'},
        body: JSON.stringify({ initData: signed, initDataUnsafe: unsafe })
      });
      const js = await r.json();
      show(js);
      if (js.ok) {
        status.textContent = "verified";
        if (js.room_id) {
          roomIdSpan.textContent = `Room - ${js.room_id}`;
          listenerCountSpan.textContent = `${js.listener_count} listener${js.listener_count > 1 ? 's' : ''}`;
          roomInfo.style.display = 'block';
        }

        // JavaScript-based profile handling (fetch from Telegram.WebApp)
        if (unsafe?.user) {
          const user = unsafe.user;
          usernameSpan.textContent = user.username || user.first_name || 'Anonymous';
          profile.style.display = 'flex';

          // Use Telegram WebApp API to get profile photo if available
          if (user.photo_url) {
            avatarImg.src = user.photo_url;
          } else if (js.profile_photo_url) {
            avatarImg.src = js.profile_photo_url;  // Fallback to server-fetched photo
          } else {
            console.log("Profile photo not available due to privacy settings.");
          }
        }
      } else {
        status.textContent = "verification failed";
      }
    } catch (e) {
      status.textContent = "network error: " + e.message;
      show({ error: e.message });
    }
  } else {
    status.textContent = "no signed initData present; open inside Telegram using web_app button (tap, don't long-press).";
  }

  // Debug info
  fetch('/debug_client', { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({ ua:navigator.userAgent, initDataUnsafe: unsafe, initDataSigned: signed ? true : false }) }).catch(()=>{});
})();
