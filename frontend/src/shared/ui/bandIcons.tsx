import type { SVGProps } from "react";

type P = SVGProps<SVGSVGElement>;

export function Sprout(props: P) {
  return (
    <svg viewBox="0 0 16 16" fill="none" aria-hidden {...props}>
      <path d="M8 14V7" stroke="currentColor" strokeWidth="1.5" />
      <path d="M8 8c-3-4-6-3-6-3 2 3 4 3 6 3Z" fill="currentColor" />
    </svg>
  );
}
export function Stem(props: P) {
  return (
    <svg viewBox="0 0 16 16" fill="none" aria-hidden {...props}>
      <path d="M8 14V4" stroke="currentColor" strokeWidth="1.5" />
      <circle cx="8" cy="4" r="2" fill="currentColor" />
    </svg>
  );
}
export function Leaf(props: P) {
  return (
    <svg viewBox="0 0 16 16" fill="none" aria-hidden {...props}>
      <path d="M4 12c6-1 8-6 8-9-4 1-8 4-8 9Z" fill="currentColor" />
    </svg>
  );
}
export function Helix(props: P) {
  return (
    <svg viewBox="0 0 16 16" fill="none" aria-hidden {...props}>
      <path d="M4 3c3 3 5 7 8 10M12 3C9 6 7 10 4 13" stroke="currentColor" strokeWidth="1.5" />
    </svg>
  );
}
export function CircleHelp(props: P) {
  return (
    <svg viewBox="0 0 16 16" fill="none" aria-hidden {...props}>
      <circle cx="8" cy="8" r="6" stroke="currentColor" />
      <path d="M8 12h.01M6.8 6.2a1.4 1.4 0 1 1 2.1 1.2c-.5.3-.9.6-.9 1.2" stroke="currentColor" />
    </svg>
  );
}
