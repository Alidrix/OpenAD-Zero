import {V2Logo} from '../components/v2/V2Logo';
import {V2_BRAND} from '../lib/v2Brand';
import '../styles/v2-theme.css';

const palette = [
  ['Background', '#FAF9F5'],
  ['Surface', '#FFFFFF'],
  ['Text', '#141413'],
  ['Muted', '#6F6B63'],
  ['Border', '#E8E6DC'],
  ['Gray', '#B1ADA1'],
  ['Orange', '#C15F3C'],
  ['Orange light', '#F28A4B'],
  ['Orange dark', '#8E3E26'],
] as const;

const principles = [
  'persistent by default',
  'human-approved operations',
  'no raw frontend commands',
  'dashboard read-only',
  'evidence-first workflow',
];

export function V2BrandPage() {
  return (
    <div className="v2-shell space-y-6">
      <header className="v2-card p-6">
        <div className="v2-header">
          <div>
            <V2Logo size={84} showText />
            <h1 className="mt-5 text-4xl font-bold">{V2_BRAND.productName}</h1>
            <p className="mt-2 text-[var(--v2-text-muted)]">{V2_BRAND.tagline}</p>
          </div>
          <span className="v2-badge v2-badge-active">V2 identity</span>
        </div>
      </header>

      <section className="grid gap-6 lg:grid-cols-2">
        <div className="v2-card p-6">
          <h2 className="v2-section-title">Product position</h2>
          <p className="mt-3 text-[var(--v2-text-muted)]">
            {V2_BRAND.productName} is the V2 interface identity for persistent Active Directory audit operations inside the {V2_BRAND.repositoryName} repository.
          </p>
          <dl className="mt-5 space-y-3 text-sm">
            <div><dt className="v2-counter-label">Repository</dt><dd className="mt-1 font-bold">{V2_BRAND.repositoryName}</dd></div>
            <div><dt className="v2-counter-label">Tagline</dt><dd className="mt-1 font-bold">{V2_BRAND.tagline}</dd></div>
          </dl>
        </div>

        <div className="v2-card p-6">
          <h2 className="v2-section-title">UX principles</h2>
          <ul className="mt-4 space-y-2">
            {principles.map(principle => <li className="v2-card-muted p-3 font-semibold" key={principle}>{principle}</li>)}
          </ul>
        </div>
      </section>

      <section className="v2-card p-6">
        <h2 className="v2-section-title">Palette</h2>
        <div className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {palette.map(([name, value]) => (
            <div className="v2-card-muted p-3" key={name}>
              <div className="h-14 rounded-2xl border border-[var(--v2-border)]" style={{background: value}} />
              <p className="mt-2 font-bold">{name}</p>
              <p className="text-sm text-[var(--v2-text-muted)]">{value}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="v2-card p-6">
        <h2 className="v2-section-title">Domain candidates</h2>
        <p className="mt-2 text-sm text-[var(--v2-text-muted)]">Candidates to verify later; this page does not claim availability.</p>
        <div className="mt-4 flex flex-wrap gap-2">
          {V2_BRAND.domainCandidates.map(domain => <span className="v2-badge" key={domain}>{domain}</span>)}
        </div>
      </section>
    </div>
  );
}
