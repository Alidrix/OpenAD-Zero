import {V2_BRAND} from '../../lib/v2Brand';

type V2LogoProps = {
  size?: number;
  showText?: boolean;
  className?: string;
};

export function V2Logo({size = 40, showText = false, className = ''}: V2LogoProps) {
  return (
    <div className={`inline-flex items-center gap-3 ${className}`}>
      <svg
        aria-label={`${V2_BRAND.productName} logo`}
        fill="none"
        height={size}
        role="img"
        viewBox="0 0 64 64"
        width={size}
        xmlns="http://www.w3.org/2000/svg"
      >
        <defs>
          <linearGradient id="v2-logo-orbit" x1="13" x2="51" y1="10" y2="54" gradientUnits="userSpaceOnUse">
            <stop stopColor="#B1ADA1" />
            <stop offset="0.55" stopColor="#C15F3C" />
            <stop offset="1" stopColor="#F28A4B" />
          </linearGradient>
          <radialGradient id="v2-logo-dot" cx="0" cy="0" r="1" gradientTransform="matrix(7 0 0 7 49 18)" gradientUnits="userSpaceOnUse">
            <stop stopColor="#F28A4B" />
            <stop offset="0.65" stopColor="#C15F3C" />
            <stop offset="1" stopColor="#8E3E26" />
          </radialGradient>
        </defs>
        <circle cx="32" cy="32" r="27" fill="#FAF9F5" stroke="#E8E6DC" strokeWidth="2" />
        <ellipse cx="32" cy="32" rx="29" ry="12" stroke="url(#v2-logo-orbit)" strokeLinecap="round" strokeWidth="2.8" transform="rotate(-24 32 32)" />
        <path d="M16 44L25 19H31L40 44H34L32.2 38.5H23.6L21.8 44H16ZM25 33.6H30.8L27.9 24.7L25 33.6Z" fill="#141413" />
        <path d="M40 19H48C55.5 19 60 23.8 60 31.4C60 39.1 55.5 44 48 44H40V19ZM46 24.3V38.7H47.7C51.8 38.7 54 36.2 54 31.4C54 26.8 51.8 24.3 47.7 24.3H46Z" fill="#141413" />
        <circle cx="49" cy="18" r="5.2" fill="url(#v2-logo-dot)" stroke="#FAF9F5" strokeWidth="2" />
      </svg>
      {showText && (
        <span className="leading-tight">
          <span className="block font-bold text-[var(--v2-text)]">{V2_BRAND.productName}</span>
          <span className="block text-xs font-medium text-[var(--v2-text-muted)]">{V2_BRAND.shortTagline}</span>
        </span>
      )}
    </div>
  );
}
