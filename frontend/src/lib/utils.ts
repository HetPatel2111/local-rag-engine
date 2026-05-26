export function clamp01(value: number): number {
  if (Number.isNaN(value)) return 0;
  return Math.min(1, Math.max(0, value));
}

export function formatMs(ms: number): string {
  if (!Number.isFinite(ms)) return "—";
  if (ms < 1000) return `${ms.toFixed(0)} ms`;
  return `${(ms / 1000).toFixed(2)} s`;
}

export function isProbablyUrl(value: string): boolean {
  return /^https?:\/\/\S+/i.test(value);
}

