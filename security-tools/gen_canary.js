#!/usr/bin/env node
// Generates a small encrypted "canary" payload using the exact same PBKDF2 + AES-256-GCM
// scheme as lock_page.js, but for a tiny known plaintext (not a full page). Used by the
// gateway page to figure out WHICH password was entered without embedding real content.
const { webcrypto } = require('crypto');
const subtle = webcrypto.subtle;
const PBKDF2_ITERATIONS = 300000;

async function deriveKey(password, salt) {
  const enc = new TextEncoder();
  const baseKey = await subtle.importKey('raw', enc.encode(password), 'PBKDF2', false, ['deriveKey']);
  return subtle.deriveKey(
    { name: 'PBKDF2', salt, iterations: PBKDF2_ITERATIONS, hash: 'SHA-256' },
    baseKey, { name: 'AES-GCM', length: 256 }, false, ['encrypt', 'decrypt']
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

async function main() {
  const [,, plaintext, password] = process.argv;
  const payload = await encryptText(plaintext, password);
  console.log(JSON.stringify(payload));
}
main();
