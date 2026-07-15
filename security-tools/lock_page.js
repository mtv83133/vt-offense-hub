#!/usr/bin/env node
/*
 * lock_page.js -- wraps an HTML page's <body> content behind a client-side
 * password gate. The entire body (all markup + inline scripts + data) is
 * AES-256-GCM encrypted with a key derived from a password via PBKDF2. The
 * ciphertext sits in the shipped HTML; nothing readable exists in the page
 * source until the correct password is entered in the browser.
 *
 * Usage:
 *   node lock_page.js <input.html> <output.html> <password>
 *
 * To change the password later, just re-run this against the ORIGINAL
 * unencrypted source file (keep a plaintext copy around for edits -- you
 * cannot easily "re-encrypt" an already-locked file without the old
 * password, since the body markup is gone from the shipped file).
 */
const fs = require('fs');
const { webcrypto } = require('crypto');
const subtle = webcrypto.subtle;

const PBKDF2_ITERATIONS = 300000;

async function deriveKey(password, salt) {
  const enc = new TextEncoder();
  const baseKey = await subtle.importKey('raw', enc.encode(password), 'PBKDF2', false, ['deriveKey']);
  return subtle.deriveKey(
    { name: 'PBKDF2', salt, iterations: PBKDF2_ITERATIONS, hash: 'SHA-256' },
    baseKey,
    { name: 'AES-GCM', length: 256 },
    false,
    ['encrypt', 'decrypt']
  );
}

function b64(buf) { return Buffer.from(buf).toString('base64'); }

async function encryptText(plaintext, password) {
  const salt = webcrypto.getRandomValues(new Uint8Array(16));
  const iv = webcrypto.getRandomValues(new Uint8Array(12));
  const key = await deriveKey(password, salt);
  const enc = new TextEncoder();
  const ciphertext = await subtle.encrypt({ name: 'AES-GCM', iv }, key, enc.encode(plaintext));
  return { salt: b64(salt), iv: b64(iv), ct: b64(ciphertext), it: PBKDF2_ITERATIONS };
}

const LOCK_CSS = `
/* ===== Password gate (injected by lock_page.js) ===== */
#vtLockOverlay{position:fixed;inset:0;z-index:99999;background:linear-gradient(135deg,#3D0A1E 0%,#1B1B2F 100%);
  display:flex;align-items:center;justify-content:center;padding:24px;}
#vtLockBox{background:#242438;border:1px solid #3A3A58;border-radius:16px;padding:40px 32px;max-width:380px;width:100%;
  box-shadow:0 12px 48px rgba(0,0,0,.6);text-align:center;}
#vtLockBox .vt-lock-icon{background:#E5751F;color:#3D0A1E;font-size:24px;font-weight:900;width:52px;height:52px;
  display:flex;align-items:center;justify-content:center;border-radius:10px;margin:0 auto 18px;}
#vtLockBox h2{color:#fff;font-size:16px;font-weight:800;letter-spacing:.5px;margin-bottom:6px;
  font-family:'Segoe UI',Arial,sans-serif;text-transform:uppercase;}
#vtLockBox p{color:#AAA8C2;font-size:12px;margin-bottom:20px;font-family:'Segoe UI',Arial,sans-serif;}
#vtLockInput{width:100%;background:#1B1B2F;border:1px solid #3A3A58;border-radius:8px;color:#fff;
  padding:12px 14px;font-size:14px;margin-bottom:12px;font-family:'Segoe UI',Arial,sans-serif;}
#vtLockInput:focus{outline:none;border-color:#E5751F;}
#vtLockBtn{width:100%;background:#E5751F;color:#3D0A1E;border:none;border-radius:8px;padding:12px;
  font-size:13px;font-weight:800;text-transform:uppercase;letter-spacing:1px;cursor:pointer;
  font-family:'Segoe UI',Arial,sans-serif;transition:filter .15s;}
#vtLockBtn:hover{filter:brightness(1.1);}
#vtLockBtn:active{filter:brightness(.95);}
#vtLockErr{color:#ff8080;font-size:11px;margin-top:10px;min-height:14px;font-family:'Segoe UI',Arial,sans-serif;}
#vtLockFoot{color:#666485;font-size:10px;margin-top:18px;font-family:'Segoe UI',Arial,sans-serif;}
`;

function buildBootstrap(payload) {
  const payloadJson = JSON.stringify(payload);
  return `
<div id="vtLockOverlay">
  <div id="vtLockBox">
    <div class="vt-lock-icon">VT</div>
    <h2>Protected Report</h2>
    <p>Internal use only. Enter the password to continue.</p>
    <input id="vtLockInput" type="password" placeholder="Password" autocomplete="off" autofocus>
    <button id="vtLockBtn" type="button">Unlock</button>
    <div id="vtLockErr"></div>
    <div id="vtLockFoot">VT Football &middot; Session unlocks automatically on other pages</div>
  </div>
</div>
<script id="vtLockPayload" type="application/json">${payloadJson}</script>
<script>
(function(){
  var PBKDF2_ITERATIONS = ${PBKDF2_ITERATIONS};
  var SS_KEY = 'vt_scout_pw_v1';

  function b64ToBytes(str) {
    var bin = atob(str);
    var bytes = new Uint8Array(bin.length);
    for (var i = 0; i < bin.length; i++) bytes[i] = bin.charCodeAt(i);
    return bytes;
  }

  function deriveKey(password, saltBytes) {
    var enc = new TextEncoder();
    return crypto.subtle.importKey('raw', enc.encode(password), 'PBKDF2', false, ['deriveKey'])
      .then(function(baseKey){
        return crypto.subtle.deriveKey(
          { name: 'PBKDF2', salt: saltBytes, iterations: PBKDF2_ITERATIONS, hash: 'SHA-256' },
          baseKey,
          { name: 'AES-GCM', length: 256 },
          false,
          ['decrypt']
        );
      });
  }

  function decryptPayload(password) {
    var payload = JSON.parse(document.getElementById('vtLockPayload').textContent);
    var salt = b64ToBytes(payload.salt);
    var iv = b64ToBytes(payload.iv);
    var ct = b64ToBytes(payload.ct);
    return deriveKey(password, salt).then(function(key){
      return crypto.subtle.decrypt({ name: 'AES-GCM', iv: iv }, key, ct);
    }).then(function(plainBuf){
      return new TextDecoder().decode(plainBuf);
    });
  }

  function reveal(html) {
    document.body.innerHTML = html;
    var scripts = Array.prototype.slice.call(document.body.querySelectorAll('script'));
    scripts.forEach(function(oldScript){
      var newScript = document.createElement('script');
      for (var i = 0; i < oldScript.attributes.length; i++) {
        var attr = oldScript.attributes[i];
        newScript.setAttribute(attr.name, attr.value);
      }
      newScript.textContent = oldScript.textContent;
      oldScript.parentNode.replaceChild(newScript, oldScript);
    });
  }

  function attemptUnlock(password, opts) {
    opts = opts || {};
    return decryptPayload(password).then(function(html){
      try { sessionStorage.setItem(SS_KEY, password); } catch(e) {}
      reveal(html);
      return true;
    }).catch(function(){
      if (!opts.silent) {
        var err = document.getElementById('vtLockErr');
        if (err) err.textContent = 'Incorrect password. Try again.';
        var input = document.getElementById('vtLockInput');
        if (input) { input.value = ''; input.focus(); }
      }
      return false;
    });
  }

  function wireUpUI() {
    var btn = document.getElementById('vtLockBtn');
    var input = document.getElementById('vtLockInput');
    if (btn) btn.addEventListener('click', function(){ attemptUnlock(input.value); });
    if (input) input.addEventListener('keydown', function(e){
      if (e.key === 'Enter') attemptUnlock(input.value);
    });
  }

  var stored = null;
  try { stored = sessionStorage.getItem(SS_KEY); } catch(e) {}
  if (stored) {
    attemptUnlock(stored, { silent: true }).then(function(ok){
      if (!ok) wireUpUI();
    });
  } else {
    wireUpUI();
  }
})();
</script>`;
}

async function main() {
  const [,, inputPath, outputPath, password] = process.argv;
  if (!inputPath || !outputPath || !password) {
    console.error('Usage: node lock_page.js <input.html> <output.html> <password>');
    process.exit(1);
  }

  const html = fs.readFileSync(inputPath, 'utf8');

  const bodyOpenMatch = html.match(/<body[^>]*>/i);
  const bodyCloseIdx = html.lastIndexOf('</body>');
  if (!bodyOpenMatch || bodyCloseIdx === -1) {
    console.error('Could not find <body>...</body> in', inputPath);
    process.exit(1);
  }
  const bodyOpenTag = bodyOpenMatch[0];
  const bodyStart = bodyOpenMatch.index + bodyOpenTag.length;
  const bodyInner = html.slice(bodyStart, bodyCloseIdx);

  const payload = await encryptText(bodyInner, password);
  const bootstrap = buildBootstrap(payload);

  const headCloseIdx = html.indexOf('</head>');
  const newHead = html.slice(0, headCloseIdx) + `<style>${LOCK_CSS}</style>\n` + html.slice(headCloseIdx, bodyOpenMatch.index);

  const newHtml = newHead + bodyOpenTag + bootstrap + '\n</body></html>';

  fs.writeFileSync(outputPath, newHtml, 'utf8');
  console.log('Locked', inputPath, '->', outputPath, `(${(bodyInner.length/1024).toFixed(1)}KB plaintext body encrypted)`);
}

main();
