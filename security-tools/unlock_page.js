#!/usr/bin/env node
/*
 * unlock_page.js -- the inverse of lock_page.js. Decrypts a locked page's
 * <body> payload back to plaintext HTML, using the same password used to
 * lock it, and strips the injected password-gate CSS/markup back out so the
 * result is (byte-for-byte) the original pre-lock source.
 *
 * This exists as a recovery path: if a plaintext `_source/` master is ever
 * lost, deleted, or out of sync, you can always regenerate it from the
 * deployed/locked file on the live site (or any locked .html on disk) as
 * long as you still know the password. The deployed files are already
 * backed up in git history, so this makes the password -- not the _source
 * folder -- the real single point of failure.
 *
 * Usage:
 *   node unlock_page.js <locked.html> <output.html> <password>
 *
 * Example (recover advance-scout.html's master from the deployed copy):
 *   node unlock_page.js advance-scout.html _source/advance-scout.html HOKIESOFF2026
 */
const fs = require('fs');
const { webcrypto } = require('crypto');
const subtle = webcrypto.subtle;

const PBKDF2_ITERATIONS = 300000;

function b64ToBytes(str) {
  return new Uint8Array(Buffer.from(str, 'base64'));
}

async function deriveKey(password, saltBytes) {
  const enc = new TextEncoder();
  const baseKey = await subtle.importKey('raw', enc.encode(password), 'PBKDF2', false, ['deriveKey']);
  return subtle.deriveKey(
    { name: 'PBKDF2', salt: saltBytes, iterations: PBKDF2_ITERATIONS, hash: 'SHA-256' },
    baseKey,
    { name: 'AES-GCM', length: 256 },
    false,
    ['decrypt']
  );
}

async function decryptPayload(payload, password) {
  const salt = b64ToBytes(payload.salt);
  const iv = b64ToBytes(payload.iv);
  const ct = b64ToBytes(payload.ct);
  const key = await deriveKey(password, salt);
  const plainBuf = await subtle.decrypt({ name: 'AES-GCM', iv }, key, ct);
  return new TextDecoder().decode(plainBuf);
}

// Must match the LOCK_CSS block injected by lock_page.js exactly, so it can
// be stripped back out to reproduce the original <head>.
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

async function main() {
  const [, , inputPath, outputPath, password] = process.argv;
  if (!inputPath || !outputPath || !password) {
    console.error('Usage: node unlock_page.js <locked.html> <output.html> <password>');
    process.exit(1);
  }

  const html = fs.readFileSync(inputPath, 'utf8');

  const payloadMatch = html.match(/<script id="vtLockPayload"[^>]*>([\s\S]*?)<\/script>/);
  if (!payloadMatch) {
    console.error('No vtLockPayload found in', inputPath, '-- is this actually a locked page?');
    process.exit(1);
  }
  const payload = JSON.parse(payloadMatch[1]);

  let bodyInner;
  try {
    bodyInner = await decryptPayload(payload, password);
  } catch (e) {
    console.error('Decryption failed -- wrong password, or the file is corrupted.');
    process.exit(1);
  }

  // Reconstruct the original <head>...</head> by stripping the injected lock CSS.
  const bodyOpenMatch = html.match(/<body[^>]*>/i);
  const headPart = html.slice(0, bodyOpenMatch.index);
  const injectedStyle = `<style>${LOCK_CSS}</style>\n`;
  const cleanHead = headPart.includes(injectedStyle)
    ? headPart.replace(injectedStyle, '')
    : headPart; // fall back to leaving it in if the exact match ever drifts

  const bodyOpenTag = bodyOpenMatch[0];
  const newHtml = cleanHead + bodyOpenTag + bodyInner + '</body>\n</html>\n';

  fs.writeFileSync(outputPath, newHtml, 'utf8');
  console.log('Unlocked', inputPath, '->', outputPath, `(${(bodyInner.length / 1024).toFixed(1)}KB plaintext body recovered)`);
}

main();
