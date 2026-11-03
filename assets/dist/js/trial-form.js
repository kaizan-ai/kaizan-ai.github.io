(function () {
var root = document.querySelector('[data-trial]');
if (!root) return;
var form = root.querySelector('form');
var more = root.querySelector('[data-trial-more]');
var legal = root.querySelector('[data-trial-legal]');
var msg = root.querySelector('[data-trial-msg]');
var submit = form.querySelector('[type=submit]');
var jsonUrl = form.getAttribute('data-mc-json');
var STORE = 'kz-utm';
root.classList.add('is-js');
var saved = {};
try { saved = JSON.parse(sessionStorage.getItem(STORE) || '{}') || {}; } catch (e) {}
var params = new URLSearchParams(window.location.search);
var fromUrl = false;
form.querySelectorAll('input[data-utm]').forEach(function (el) {
if (params.has(el.getAttribute('data-utm'))) fromUrl = true;
});
form.querySelectorAll('input[data-utm]').forEach(function (el) {
var key = el.getAttribute('data-utm');
var val = fromUrl ? (params.get(key) || '') : (saved[key] || '');
el.value = val.slice(0, 255);
saved[key] = el.value;
});
if (fromUrl) {
try { sessionStorage.setItem(STORE, JSON.stringify(saved)); } catch (e) {}
}
var required = ['FNAME', 'LNAME', 'EMAIL', 'PHONE'].map(function (n) {
return form.querySelector('[name=' + n + ']');
});
function setOpen(open) {
more.classList.toggle('is-open', open);
legal.classList.toggle('is-open', open);
if (open) more.removeAttribute('inert'); else more.setAttribute('inert', '');
}
function check() {
var open = required.every(function (el) { return el.value.trim() !== ''; });
if (open || !more.classList.contains('is-open')) setOpen(open);
}
required.forEach(function (el) { el.addEventListener('input', check); });
check();
function show(text) {
msg.textContent = text;
msg.classList.toggle('is-shown', !!text);
}
function clean(m) {
var d = document.createElement('div');
d.innerHTML = String(m || '').replace(/^\d+\s*-\s*/, '');
return (d.textContent || '').trim();
}
form.addEventListener('submit', function (e) {
if (!jsonUrl) return;
e.preventDefault();
if (!form.reportValidity()) { setOpen(true); return; }
show('');
submit.disabled = true;
var body = new URLSearchParams(new FormData(form)).toString();
var cb = 'kzTrial_' + Date.now();
var s = document.createElement('script');
function finish() {
submit.disabled = false;
delete window[cb];
if (s.parentNode) s.parentNode.removeChild(s);
}
window[cb] = function (data) {
finish();
if (data && data.result === 'success') {
try { sessionStorage.removeItem(STORE); } catch (e) {}
if (window.dataLayer) window.dataLayer.push({ event: 'trial_signup' });
window.location.href = 'https://kaizan.ai/confirmation';
} else {
show(clean(data && data.msg) || 'Something went wrong, please try again.');
}
};
s.onerror = function () { finish(); show('Network error, please try again.'); };
s.src = jsonUrl + '&' + body + '&c=' + cb;
document.body.appendChild(s);
});
})();
