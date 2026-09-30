// 숫자 표기. 빼기는 하이픈이 아니라 U+2212(−)를 쓴다.

const MINUS = "−";

function signed(text: string, value: number, sign: boolean) {
  if (value < 0) return MINUS + text.replace("-", "");
  return sign && value > 0 ? `+${text}` : text;
}

export function pct(value: number | null, digits = 1, sign = true) {
  if (value === null || !Number.isFinite(value)) return "—";
  return signed(`${(value * 100).toFixed(digits)}%`, value, sign);
}

export function ratio(value: number | null, digits = 2) {
  if (value === null || !Number.isFinite(value)) return "—";
  return signed(value.toFixed(digits), value, false);
}

export function int(value: number) {
  return value.toLocaleString("en-US");
}

export function money(value: number, digits = 0) {
  return signed(
    `$${Math.abs(value).toLocaleString("en-US", { minimumFractionDigits: digits, maximumFractionDigits: digits })}`,
    value,
    false,
  );
}

export function price(value: number) {
  return value.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

export function qty(value: number) {
  return value.toLocaleString("en-US", { maximumSignificantDigits: 6 });
}

export function ordinal(n: number) {
  const r = Math.round(n);
  const tens = r % 100;
  const suffix = tens >= 11 && tens <= 13 ? "th" : ({ 1: "st", 2: "nd", 3: "rd" }[r % 10] ?? "th");
  return `${r}${suffix}`;
}

// 백엔드 시각은 모두 UTC ISO 문자열이다.
export function utcDate(iso: string) {
  return iso.slice(0, 10);
}

export function utcDateTime(iso: string) {
  return iso.slice(0, 16).replace("T", " ");
}

export function longDate(iso: string) {
  return new Date(iso).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
    timeZone: "UTC",
  });
}
