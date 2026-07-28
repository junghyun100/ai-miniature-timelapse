/**
 * Source Revision Computation Module (WP-4)
 *
 * Computes SHA-256 source revision matching Python src/domain.py.
 * Implements canonical JSON serialization per Section 14.1 of the spec:
 * - Filter to prompt-affecting included fields
 * - Recursively sort all object keys alphabetically
 * - UTF-8 encode with NFC Unicode normalization
 * - No insignificant whitespace (compact separators)
 * - SHA-256 hash with "sha256:" prefix
 */

import { INCLUDED_SOURCE_REVISION_KEYS } from './app.js';
export { INCLUDED_SOURCE_REVISION_KEYS };

export function normalizeUnicode(value) {
  if (typeof value === 'string') {
    return value.normalize('NFC');
  }
  if (Array.isArray(value)) {
    return value.map(normalizeUnicode);
  }
  if (value !== null && typeof value === 'object') {
    const result = {};
    for (const [k, v] of Object.entries(value)) {
      result[k] = normalizeUnicode(v);
    }
    return result;
  }
  return value;
}

export function sortKeysRecursive(obj) {
  if (Array.isArray(obj)) {
    return obj.map(sortKeysRecursive);
  }
  if (obj !== null && typeof obj === 'object') {
    const sorted = {};
    for (const key of Object.keys(obj).sort()) {
      sorted[key] = sortKeysRecursive(obj[key]);
    }
    return sorted;
  }
  return obj;
}

export function filterIncludedFields(sourceDraft) {
  if (!sourceDraft || typeof sourceDraft !== 'object') {
    return {};
  }
  const filtered = {};
  for (const [key, value] of Object.entries(sourceDraft)) {
    if (INCLUDED_SOURCE_REVISION_KEYS.has(key) && value !== undefined) {
      filtered[key] = value;
    }
  }
  return filtered;
}

export function canonicalJSON(sourceDraft) {
  const filtered = filterIncludedFields(sourceDraft);
  const normalized = sortKeysRecursive(normalizeUnicode(filtered));
  return JSON.stringify(normalized);
}

/**
 * Pure JS synchronous SHA-256 implementation.
 * 100% deterministic and cross-platform compatible with Python hashlib.sha256.
 */
export function sha256Sync(str) {
  const utf8 = new TextEncoder().encode(str);
  const K = [
    0x428a2f98, 0x71374491, 0xb5c0fbcf, 0xe9b5dba5, 0x3956c25b, 0x59f111f1, 0x923f82a4, 0xab1c5ed5,
    0xd807aa98, 0x12835b01, 0x243185be, 0x550c7dc3, 0x72be5d74, 0x80deb1fe, 0x9bdc06a7, 0xc19bf174,
    0xe49b69c1, 0xefbe4786, 0x0fc19dc6, 0x240ca1cc, 0x2de92c6f, 0x4a7484aa, 0x5cb0a9dc, 0x76f988da,
    0x983e5152, 0xa831c66d, 0xb00327c8, 0xbf597fc7, 0xc6e00bf3, 0xd5a79147, 0x06ca6351, 0x14292967,
    0x27b70a85, 0x2e1b2138, 0x4d2c6dfc, 0x53380d13, 0x650a7354, 0x766a0abb, 0x81c2c92e, 0x92722c85,
    0xa2bfe8a1, 0xa81a664b, 0xc24b8b70, 0xc76c51a3, 0xd192e819, 0xd6990624, 0xf40e3585, 0x106aa070,
    0x19a4c116, 0x1e376c08, 0x2748774c, 0x34b0bcb5, 0x391c0cb3, 0x4ed8aa4a, 0x5b9cca4f, 0x682e6ff3,
    0x748f82ee, 0x78a5636f, 0x84c87814, 0x8cc70208, 0x90befffa, 0xa4506ceb, 0xbef9a3f7, 0xc67178f2
  ];

  let H0 = 0x6a09e667, H1 = 0xbb67ae85, H2 = 0x3c6ef372, H3 = 0xa54ff53a;
  let H4 = 0x510e527f, H5 = 0x9b05688c, H6 = 0x1f83d9ab, H7 = 0x5be0cd19;

  const len = utf8.length;
  const bitLenHi = Math.floor(len / 0x20000000);
  const bitLenLo = (len << 3) >>> 0;

  const paddedLen = (((len + 8) >> 6) + 1) << 6;
  const blocks = new Uint8Array(paddedLen);
  blocks.set(utf8);
  blocks[len] = 0x80;

  const view = new DataView(blocks.buffer);
  view.setUint32(paddedLen - 8, bitLenHi, false);
  view.setUint32(paddedLen - 4, bitLenLo, false);

  const W = new Int32Array(64);

  function rightRotate(n, bits) {
    return ((n >>> bits) | (n << (32 - bits))) >>> 0;
  }

  for (let i = 0; i < paddedLen; i += 64) {
    for (let t = 0; t < 16; t++) {
      W[t] = view.getInt32(i + t * 4, false);
    }
    for (let t = 16; t < 64; t++) {
      const s0 = (rightRotate(W[t - 15], 7) ^ rightRotate(W[t - 15], 18) ^ (W[t - 15] >>> 3)) >>> 0;
      const s1 = (rightRotate(W[t - 2], 17) ^ rightRotate(W[t - 2], 19) ^ (W[t - 2] >>> 10)) >>> 0;
      W[t] = (W[t - 16] + s0 + W[t - 7] + s1) | 0;
    }

    let a = H0, b = H1, c = H2, d = H3, e = H4, f = H5, g = H6, h = H7;

    for (let t = 0; t < 64; t++) {
      const S1 = (rightRotate(e, 6) ^ rightRotate(e, 11) ^ rightRotate(e, 25)) >>> 0;
      const ch = ((e & f) ^ (~e & g)) >>> 0;
      const temp1 = (h + S1 + ch + K[t] + W[t]) | 0;
      const S0 = (rightRotate(a, 2) ^ rightRotate(a, 13) ^ rightRotate(a, 22)) >>> 0;
      const maj = ((a & b) ^ (a & c) ^ (b & c)) >>> 0;
      const temp2 = (S0 + maj) | 0;

      h = g;
      g = f;
      f = e;
      e = (d + temp1) | 0;
      d = c;
      c = b;
      b = a;
      a = (temp1 + temp2) | 0;
    }

    H0 = (H0 + a) | 0;
    H1 = (H1 + b) | 0;
    H2 = (H2 + c) | 0;
    H3 = (H3 + d) | 0;
    H4 = (H4 + e) | 0;
    H5 = (H5 + f) | 0;
    H6 = (H6 + g) | 0;
    H7 = (H7 + h) | 0;
  }

  const toHex = (n) => (n >>> 0).toString(16).padStart(8, "0");
  return toHex(H0) + toHex(H1) + toHex(H2) + toHex(H3) + toHex(H4) + toHex(H5) + toHex(H6) + toHex(H7);
}

export function computeSourceRevisionSync(sourceDraft) {
  const canonical = canonicalJSON(sourceDraft);
  const hashHex = sha256Sync(canonical);
  return `sha256:${hashHex}`;
}

export async function computeSourceRevision(sourceDraft) {
  if (typeof globalThis !== 'undefined' && globalThis.crypto?.subtle?.digest) {
    const canonical = canonicalJSON(sourceDraft);
    const encoder = new TextEncoder();
    const data = encoder.encode(canonical);
    const hashBuffer = await globalThis.crypto.subtle.digest('SHA-256', data);
    const hashArray = Array.from(new Uint8Array(hashBuffer));
    const hashHex = hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
    return `sha256:${hashHex}`;
  }
  return computeSourceRevisionSync(sourceDraft);
}
