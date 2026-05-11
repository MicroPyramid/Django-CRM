export const AVATAR_GRADIENTS = [
  'linear-gradient(135deg, #a78bfa, #7c3aed)', // 0 purple
  'linear-gradient(135deg, #f472b6, #db2777)', // 1 pink
  'linear-gradient(135deg, #34d399, #059669)', // 2 green
  'linear-gradient(135deg, #60a5fa, #2563eb)', // 3 blue
  'linear-gradient(135deg, #fbbf24, #ef4444)', // 4 orange-red
  'linear-gradient(135deg, #67e8f9, #0891b2)', // 5 cyan
  'linear-gradient(135deg, #fcd34d, #d97706)'  // 6 amber
];

export const WORKSPACE_GRADIENT = 'linear-gradient(135deg, #ea580c, #c2410c)';

// Stable string hash → bucket [0,6]. djb2-ish; only needs to be deterministic & well-spread.
export function gradientFor(seed) {
  if (seed == null) return AVATAR_GRADIENTS[0];
  const s = String(seed);
  let h = 5381;
  for (let i = 0; i < s.length; i++) {
    h = ((h << 5) + h + s.charCodeAt(i)) | 0;
  }
  return AVATAR_GRADIENTS[Math.abs(h) % AVATAR_GRADIENTS.length];
}
