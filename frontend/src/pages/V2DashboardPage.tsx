import {useCallback, useEffect, useMemo, useState} from 'react';
import {Link} from 'react-router-dom';
import {V2Logo} from '../components/v2/V2Logo';
import {getV2DashboardSummary, type V2DashboardSummary, type V2SignalCounters} from '../lib/v2DashboardApi';
import {V2_BRAND} from '../lib/v2Brand';
import {listScans, type V2Scan} from '../lib/v2ScansApi';
import '../styles/v2-theme.css';

const ACTIVE_STATUSES = new Set(['queued', 'running', 'stopping']);
const SIGNAL_KEYS: (keyof V2SignalCounters)[] = ['smb_open', 'ldap_open', 'kerberos_open', 'http_open', 'rdp_open', 'winrm_open', 'mssql_open', 'ssh_open'];

function percent(value: number | undefined | null) {
  return Math.max(0, Math.min(100, Number(value || 0)));
}

function StatusDot({active}: {active: boolean}) {
  return <span className="v2-orbit-dot" data-active={active} />;
}

function ProgressBar({value}: {value: number}) {
  return <div className="v2-progress"><div className="v2-progress-bar" style={{width: `${percent(value)}%`}} /></div>;
}

function CounterCard({label, value, active = false}: {label: string; value: number; active?: boolean}) {
  return <div className="v2-card p-5"><div className="flex items-center justify-between gap-3"><p className="v2-counter-label">{label}</p><StatusDot active={active} /></div><p className="v2-counter mt-4">{value}</p></div>;
}

function MiniMetric({label, value}: {label: string; value: number}) {
  return <div className="v2-card-muted p-4"><p className="v2-counter-label">{label}</p><p className="mt-2 text-2xl font-bold">{value}</p></div>;
}

function ScanRow({scan}: {scan: V2Scan}) {
  return <div className="rounded-2xl border border-[var(--v2-border)] bg-[var(--v2-bg)] p-4"><div className="flex flex-wrap items-center justify-between gap-3"><div><p className="font-semibold text-[#141413]">{scan.name}</p><p className="text-sm text-[#6F6B63]">{scan.current_step || scan.tool_name || scan.scan_type}</p></div><span className="v2-badge">{scan.status}</span></div><div className="mt-3"><ProgressBar value={scan.progress_percent} /></div></div>;
}

export function V2DashboardPage() {
  const [scans, setScans] = useState<V2Scan[]>([]);
  const [allScans, setAllScans] = useState<V2Scan[]>([]);
  const [summary, setSummary] = useState<V2DashboardSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const refresh = useCallback(async () => {
    setError('');
    try {
      const [visible, withDeleted, dashboardSummary] = await Promise.all([listScans(false), listScans(true), getV2DashboardSummary({includeDeleted: true, limitRecent: 5})]);
      setScans(visible);
      setAllScans(withDeleted);
      setSummary(dashboardSummary);
    } catch (err) {
      setError(String(err));
      try {
        const [visible, withDeleted] = await Promise.all([listScans(false), listScans(true)]);
        setScans(visible);
        setAllScans(withDeleted);
      } catch (fallbackErr) {
        setError(`${String(err)}; fallback failed: ${String(fallbackErr)}`);
      }
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { refresh(); }, [refresh]);

  const activeScans = useMemo(() => scans.filter(scan => ACTIVE_STATUSES.has(scan.status)), [scans]);
  const hasActiveScans = activeScans.length > 0;

  useEffect(() => {
    if (!hasActiveScans) return undefined;
    const timer = window.setInterval(() => refresh().catch(() => undefined), 2000);
    return () => window.clearInterval(timer);
  }, [hasActiveScans, refresh]);

  const fallbackCounts = useMemo(() => ({
    total: scans.length,
    active: activeScans.length,
    queued: scans.filter(scan => scan.status === 'queued').length,
    running: scans.filter(scan => scan.status === 'running').length,
    completed: scans.filter(scan => scan.status === 'completed').length,
    failed: scans.filter(scan => scan.status === 'failed').length,
    stopped: scans.filter(scan => scan.status === 'stopped').length,
    deleted: allScans.filter(scan => scan.status === 'deleted' || scan.deleted_at).length,
  }), [activeScans.length, allScans, scans]);
  const counts = summary?.scans || fallbackCounts;

  const averageActiveProgress = activeScans.length ? Math.round(activeScans.reduce((sum, scan) => sum + percent(scan.progress_percent), 0) / activeScans.length) : 0;
  const recentScans = summary?.recent_scans || [...allScans].sort((left, right) => new Date(right.created_at).getTime() - new Date(left.created_at).getTime()).slice(0, 5);
  const latestScan = recentScans[0];

  return (
    <div className="v2-shell space-y-6">
      <header className="v2-card p-6">
        <div className="v2-header">
          <div><V2Logo size={52} showText /><h1 className="mt-5 text-4xl font-bold">{V2_BRAND.productName}</h1><p className="mt-2 text-[var(--v2-text-muted)]">{V2_BRAND.tagline}</p></div>
          <div className="flex flex-wrap gap-2"><Link className="v2-button v2-button-primary" to="/scans">Open Scan Library</Link><Link className="v2-button v2-button-secondary" to="/v2-parsed-data">View Parsed Data</Link><Link className="v2-button v2-button-secondary" to="/v2-recommendations">View Recommendations</Link></div>
        </div>
      </header>

      {error && <div className="rounded-2xl border border-amber-200 bg-amber-50 p-4 text-amber-800">{error}</div>}
      {loading && <div className="rounded-2xl border border-[#E8E6DC] bg-white p-4 text-[#6F6B63]">Loading V2 scan telemetry...</div>}

      <section className="grid gap-4 md:grid-cols-3 xl:grid-cols-8"><CounterCard label="Total scans" value={counts.total} /><CounterCard active={counts.active > 0} label="Active scans" value={counts.active} /><CounterCard label="Queued" value={counts.queued} /><CounterCard label="Running" value={counts.running} /><CounterCard label="Completed" value={counts.completed} /><CounterCard label="Failed" value={counts.failed} /><CounterCard label="Stopped" value={counts.stopped} /><CounterCard label="Deleted" value={counts.deleted} /></section>

      <section className="grid gap-6 xl:grid-cols-2"><div className="v2-card p-6"><h2 className="v2-section-title">Mission Control status</h2><p className="mt-2 text-sm text-[var(--v2-text-muted)]">Read-only telemetry from persisted V2 scans and normalized parsing tables. The dashboard never enqueues work, triggers parsing, or sends raw commands.</p><div className="mt-5 grid gap-3 sm:grid-cols-2"><div className="v2-card-muted p-4"><p className="v2-counter-label">Realtime hints</p><p className="mt-2 font-bold">WebSocket + active polling</p></div><div className="v2-card-muted p-4"><p className="v2-counter-label">Execution model</p><p className="mt-2 font-bold">Read-only dashboard</p></div></div></div><div className="v2-card p-6"><h2 className="v2-section-title">Persistence guarantee</h2><p className="mt-2 text-sm text-[var(--v2-text-muted)]">PostgreSQL remains the source of truth for scan lifecycle, parsed assets, services, signals, diagnostics, and recovery after refresh.</p><Link className="mt-5 inline-flex text-sm font-bold text-[var(--v2-orange)]" to="/scans">Review persisted Scan Library →</Link></div></section>

      {summary && <><section className="grid gap-6 xl:grid-cols-[1fr_1fr_1fr]"><div className="v2-card p-6"><h2 className="v2-section-title">Parsed Intelligence</h2><div className="mt-5 grid gap-3 sm:grid-cols-2"><MiniMetric label="Parsed assets" value={summary.parsed.assets} /><MiniMetric label="Parsed services" value={summary.parsed.services} /><MiniMetric label="Parsed signals" value={summary.parsed.signals} /><MiniMetric label="Parse diagnostics" value={summary.parsed.diagnostics} /></div></div><div className="v2-card p-6"><h2 className="v2-section-title">AD Surface</h2><div className="mt-5 grid gap-3 sm:grid-cols-2"><MiniMetric label="SMB hosts" value={summary.ad_surface.smb_hosts} /><MiniMetric label="LDAP hosts" value={summary.ad_surface.ldap_hosts} /><MiniMetric label="Kerberos hosts" value={summary.ad_surface.kerberos_hosts} /><MiniMetric label="WinRM hosts" value={summary.ad_surface.winrm_hosts} /><MiniMetric label="RDP hosts" value={summary.ad_surface.rdp_hosts} /><MiniMetric label="DC hints" value={summary.ad_surface.domain_controller_hints} /></div></div><div className="v2-card p-6"><h2 className="v2-section-title">Asset OS summary</h2><div className="mt-5 grid gap-3"><MiniMetric label="Windows hosts" value={summary.assets.windows_hosts} /><MiniMetric label="Linux hosts" value={summary.assets.linux_hosts} /><MiniMetric label="Unknown hosts" value={summary.assets.unknown_hosts} /></div></div></section>

      <section className="grid gap-6 xl:grid-cols-3"><div className="v2-card p-6"><h2 className="v2-section-title">Signal Matrix</h2><div className="mt-5 grid gap-2">{SIGNAL_KEYS.map(key => <div className="flex items-center justify-between rounded-xl bg-[#FAF9F5] p-3" key={key}><span className="font-semibold">{key}</span><span className="v2-badge">{summary.signals[key]}</span></div>)}</div></div><div className="v2-card p-6"><h2 className="v2-section-title">Top Services</h2><h3 className="mt-4 font-semibold">Top ports</h3><div className="mt-2 space-y-2">{summary.services.top_ports.length === 0 ? <p className="text-sm text-[#6F6B63]">No ports parsed yet.</p> : summary.services.top_ports.map(port => <div className="flex justify-between rounded-xl bg-[#FAF9F5] p-3" key={`${port.protocol}-${port.port}`}><span>{port.port}/{port.protocol}</span><b>{port.count}</b></div>)}</div><h3 className="mt-4 font-semibold">Top service names</h3><div className="mt-2 space-y-2">{summary.services.top_service_names.length === 0 ? <p className="text-sm text-[#6F6B63]">No service names parsed yet.</p> : summary.services.top_service_names.map(service => <div className="flex justify-between rounded-xl bg-[#FAF9F5] p-3" key={service.service_name}><span>{service.service_name}</span><b>{service.count}</b></div>)}</div></div><div className="v2-card p-6"><h2 className="v2-section-title">Diagnostics panel</h2><div className="mt-5 space-y-3">{summary.recent_diagnostics.length === 0 ? <p className="text-sm text-[#6F6B63]">No parsing diagnostics.</p> : summary.recent_diagnostics.map(item => <Link className="block rounded-xl bg-[#FAF9F5] p-3" key={item.id} to={`/v2-parsed-data?scan_id=${encodeURIComponent(item.scan_id)}`}><b>{item.level}</b><p className="text-sm text-[#6F6B63]">{item.message}</p></Link>)}</div><Link className="mt-5 inline-flex text-sm font-bold text-[var(--v2-orange)]" to="/v2-parsed-data">Open parsed data →</Link></div></section></>}

      <section className="grid gap-6 xl:grid-cols-[1.3fr_0.7fr]"><div className="v2-card p-6"><div className="flex items-center justify-between gap-3"><div><h2 className="v2-section-title">Active scans</h2><p className="text-sm text-[#6F6B63]">Average active progress: {averageActiveProgress}%</p></div><StatusDot active={hasActiveScans} /></div><div className="mt-5 space-y-3">{activeScans.length === 0 ? <p className="rounded-2xl bg-[#FAF9F5] p-4 text-[#6F6B63]">No queued, running, or stopping scans.</p> : activeScans.map(scan => <ScanRow key={scan.id} scan={scan} />)}</div></div><div className="v2-card p-6"><h2 className="v2-section-title">Recent scans</h2><p className="mt-1 text-sm text-[#6F6B63]">Latest: {latestScan ? `${latestScan.name} · ${new Date(latestScan.created_at).toLocaleString()}` : 'n/a'}</p><div className="mt-5 space-y-3">{recentScans.length === 0 ? <p className="text-[#6F6B63]">No persisted scans yet.</p> : recentScans.map(scan => <div key={scan.id} className="flex items-center justify-between gap-3 rounded-2xl bg-[#FAF9F5] p-3"><div><p className="font-semibold">{scan.name}</p><p className="text-xs text-[#6F6B63]">{scan.status} · {percent(scan.progress_percent)}%</p></div><Link className="text-sm font-semibold text-[#C15F3C]" to={`/v2-parsed-data?scan_id=${encodeURIComponent(scan.id)}`}>Parsed data</Link></div>)}</div></div></section>

      <section className="v2-safety-banner"><p>PostgreSQL is the source of truth</p><p>No parsing trigger from dashboard</p><p>No RQ job from dashboard</p><p>No subprocess</p></section>
    </div>
  );
}
