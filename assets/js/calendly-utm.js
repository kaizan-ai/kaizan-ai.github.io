/* Calendly attribution — captures UTMs from the landing URL and forwards
   them to any Calendly link, so bookings carry the campaign that drove them.
   UK-only: /demo/ reads the same sessionStorage key to tag its own
   (base64-obfuscated) Calendly redirect — see render_demo() in build.py. */
(function () {
  var KEYS = ['utm_source', 'utm_medium', 'utm_campaign', 'utm_content', 'utm_term'];
  var STORE = 'calendly_utms';

  // 1. Capture UTMs from the current page URL and remember them for this visit
  var params = new URLSearchParams(window.location.search);
  var saved = {};
  try { saved = JSON.parse(sessionStorage.getItem(STORE) || '{}'); } catch (e) {}

  var found = false;
  KEYS.forEach(function (k) {
    var v = params.get(k);
    if (v) { saved[k] = v; found = true; }
  });
  if (found) {
    try { sessionStorage.setItem(STORE, JSON.stringify(saved)); } catch (e) {}
  }

  // 2. Append the saved UTMs to every link that points to Calendly
  document.addEventListener('DOMContentLoaded', function () {
    document.querySelectorAll('a[href*="calendly.com"]').forEach(function (a) {
      try {
        var url = new URL(a.href);
        KEYS.forEach(function (k) {
          if (saved[k]) url.searchParams.set(k, saved[k]);
        });
        a.href = url.toString();
      } catch (e) {}
    });
  });
})();
