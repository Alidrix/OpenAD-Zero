import {useCallback, useEffect, useMemo, useState} from 'react';
import {
  deleteScan,
  enqueueDemoScan,
  getScan,
  listScanArtifacts,
  listScanEvents,
  listScans,
  renameScan,
  stopScan,
  type V2Scan,
  type V2ScanArtifact,
  type V2ScanEvent,
} from '../lib/v2ScansApi';
import {V2Logo} from '../components/v2/V2Logo';
import {connectScanSocket} from '../lib/v2ScanSocket';
import '../styles/v2-theme.css';

const ACTIVE_STATUSES = new Set(['queued', 'running', 'stopping']);
const DEMO_RUN_STATUSES = new Set(['draft', 'stopped', 'failed', 'completed']);
const STOP_DISABLED_STATUSES = new Set(['stopped', 'completed', 'deleted']);

function pct(value: number | undefined | null) {
  return Math.max(0, Math.min(100, Number(value || 0)));
}

function ScanProgressBar({scan}: {scan: V2Scan}) {
  const value = pct(scan.progress_percent);

  return (
    <div>
      <div className="v2-progress">
        <div className="v2-progress-bar" style={{width: `${value}%`}} />
      </div>
      <div className="mt-1 text-xs text-slate-500">
        {value}%{scan.current_step ? ` · ${scan.current_step}` : ''}
      </div>
    </div>
  );
}

function ScanStatusBadge({status}: {status: string}) {
  const tone = ACTIVE_STATUSES.has(status)
    ? 'bg-blue-100 text-blue-700 dark:bg-blue-950 dark:text-blue-200'
    : status === 'completed'
      ? 'bg-green-100 text-green-700 dark:bg-green-950 dark:text-green-200'
      : status === 'deleted'
        ? 'bg-rose-100 text-rose-700 dark:bg-rose-950 dark:text-rose-200'
        : 'bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-200';

  const v2Tone = ACTIVE_STATUSES.has(status) ? 'v2-badge-active' : status === 'completed' ? 'v2-badge-success' : status === 'deleted' || status === 'failed' ? 'v2-badge-danger' : '';

  return <span className={`v2-badge ${v2Tone} ${tone}`}>{status}</span>;
}

function ScanActions({
  scan,
  onInspect,
  onRename,
  onStop,
  onDelete,
  onRunDemo,
  onRecommendations,
  onParsedData,
}: {
  scan: V2Scan;
  onInspect: () => void;
  onRename: () => void;
  onStop: () => void;
  onDelete: () => void;
  onRunDemo: () => void;
  onRecommendations: () => void;
  onParsedData: () => void;
}) {
  const canRunDemo = DEMO_RUN_STATUSES.has(scan.status);

  return (
    <div className="flex flex-wrap gap-2">
      <button className="v2-button v2-button-secondary" onClick={onInspect}>
        Inspect
      </button>
      <button className="v2-button v2-button-secondary" onClick={onRename}>
        Rename
      </button>
      <button className="v2-button v2-button-secondary" onClick={onRecommendations}>
        View recommendations
      </button>
      <button className="v2-button v2-button-secondary" onClick={onParsedData}>
        View parsed data
      </button>
      <button className="v2-button v2-button-secondary" disabled={!canRunDemo} onClick={onRunDemo}>
        Run demo progress
      </button>
      <button className="v2-button v2-button-secondary" disabled={STOP_DISABLED_STATUSES.has(scan.status)} onClick={onStop}>
        Stop
      </button>
      <button className="v2-button v2-button-secondary" disabled={scan.status === 'deleted'} onClick={onDelete}>
        Delete
      </button>
    </div>
  );
}

function ScanEventsTimeline({events}: {events: V2ScanEvent[]}) {
  if (events.length === 0) {
    return <p className="text-sm text-slate-500">No events yet.</p>;
  }

  return (
    <div className="mt-2 max-h-80 space-y-2 overflow-auto">
      {events.map(event => (
        <div key={event.id} className="rounded-xl bg-slate-50 p-3 text-sm dark:bg-slate-800">
          <div className="flex justify-between gap-2">
            <b>{event.event_type}</b>
            <span className="text-xs text-slate-500">{new Date(event.created_at).toLocaleString()}</span>
          </div>
          <p>{event.message}</p>
          {(event.payload_json || event.payload) && (
            <pre className="mt-2 overflow-auto text-xs">{JSON.stringify(event.payload_json || event.payload, null, 2)}</pre>
          )}
        </div>
      ))}
    </div>
  );
}

function ScanArtifactsList({artifacts}: {artifacts: V2ScanArtifact[]}) {
  if (artifacts.length === 0) {
    return <p className="text-sm text-slate-500">No artifacts.</p>;
  }

  return (
    <div className="space-y-2">
      {artifacts.map(artifact => (
        <p key={artifact.id} className="break-all text-xs">
          {artifact.artifact_type}: {artifact.path}
        </p>
      ))}
    </div>
  );
}

function ScanDetailsPanel({
  scan,
  onClose,
  onScanChange,
}: {
  scan: V2Scan;
  onClose: () => void;
  onScanChange: (scan: V2Scan) => void;
}) {
  const [events, setEvents] = useState<V2ScanEvent[]>([]);
  const [artifacts, setArtifacts] = useState<V2ScanArtifact[]>([]);
  const [socketStatus, setSocketStatus] = useState<'connected' | 'disconnected' | 'error'>('disconnected');

  const refresh = useCallback(async () => {
    const [fresh, nextEvents, nextArtifacts] = await Promise.all([
      getScan(scan.id),
      listScanEvents(scan.id),
      listScanArtifacts(scan.id),
    ]);

    onScanChange(fresh);
    setEvents(nextEvents);
    setArtifacts(nextArtifacts);
  }, [scan.id, onScanChange]);

  useEffect(() => {
    refresh().catch(() => undefined);
  }, [refresh]);

  useEffect(() => {
    const connection = connectScanSocket(
      scan.id,
      event => {
        setEvents(old => (old.some(existing => existing.id === event.id) ? old : [...old, event]));

        if (event.status || event.progress_percent !== undefined || event.current_step) {
          onScanChange({
            ...scan,
            status: event.status || scan.status,
            progress_percent: event.progress_percent ?? scan.progress_percent,
            current_step: event.current_step ?? scan.current_step,
          });
        }
      },
      {replay: false, onStatus: setSocketStatus},
    );

    return () => connection.close();
  }, [scan, onScanChange]);

  return (
    <aside className="v2-card space-y-4 p-5">
      <div className="flex items-start justify-between gap-3">
        <div>
          <h2 className="text-xl font-bold">{scan.name}</h2>
          <p className="text-sm text-slate-500">
            {scan.scan_type} · {scan.tool_name || 'no tool'} · Realtime {socketStatus}
          </p>
        </div>
        <button className="v2-button v2-button-secondary" onClick={onClose}>
          Close
        </button>
      </div>

      <ScanStatusBadge status={scan.status} />
      <ScanProgressBar scan={scan} />

      <button className="v2-button v2-button-secondary" onClick={() => refresh()}>
        Manual refresh
      </button>

      <div className="grid gap-3 md:grid-cols-2">
        <div>
          <h3 className="font-semibold">Lifecycle</h3>
          <p className="text-sm">Created: {new Date(scan.created_at).toLocaleString()}</p>
          <p className="text-sm">Started: {scan.started_at ? new Date(scan.started_at).toLocaleString() : 'n/a'}</p>
          <p className="text-sm">Finished: {scan.finished_at ? new Date(scan.finished_at).toLocaleString() : 'n/a'}</p>
          <p className="text-sm">Stopped: {scan.stopped_at ? new Date(scan.stopped_at).toLocaleString() : 'n/a'}</p>
        </div>

        <div>
          <h3 className="font-semibold">Artifacts</h3>
          <ScanArtifactsList artifacts={artifacts} />
        </div>
      </div>

      <div>
        <h3 className="font-semibold">Events timeline</h3>
        <ScanEventsTimeline events={events} />
      </div>
    </aside>
  );
}

export function ScanLibrary() {
  const [scans, setScans] = useState<V2Scan[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [includeDeleted, setIncludeDeleted] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const selected = useMemo(() => scans.find(scan => scan.id === selectedId) || null, [scans, selectedId]);
  const hasActiveScans = scans.some(scan => ACTIVE_STATUSES.has(scan.status));

  const refresh = useCallback(async () => {
    setLoading(true);
    setError('');

    try {
      setScans(await listScans(includeDeleted));
    } catch (err) {
      setError(String(err));
    } finally {
      setLoading(false);
    }
  }, [includeDeleted]);

  const replace = useCallback((scan: V2Scan) => {
    setScans(old => old.map(item => (item.id === scan.id ? scan : item)));
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  useEffect(() => {
    if (!hasActiveScans) {
      return undefined;
    }

    const timer = window.setInterval(() => refresh().catch(() => undefined), 2000);
    return () => window.clearInterval(timer);
  }, [hasActiveScans, refresh]);

  async function rename(scan: V2Scan) {
    const name = prompt('New scan name', scan.name);
    if (!name) {
      return;
    }

    replace(await renameScan(scan.id, name));
    await refresh();
  }

  async function stop(scan: V2Scan) {
    replace(await stopScan(scan.id));
    await refresh();
  }

  async function runDemo(scan: V2Scan) {
    if (!DEMO_RUN_STATUSES.has(scan.status)) {
      return;
    }

    replace(await enqueueDemoScan(scan.id));
    await refresh();
  }

  async function remove(scan: V2Scan) {
    if (!confirm(`Delete ${scan.name}?`)) {
      return;
    }

    replace(await deleteScan(scan.id));
    await refresh();
  }

  return (
    <div className="v2-shell space-y-6">
      <div className="v2-card p-6">
        <div className="v2-header">
          <div>
            <V2Logo size={44} showText />
            <h1 className="mt-4 text-3xl font-bold">Scan Library</h1>
            <p className="text-[var(--v2-text-muted)]">Persisted scan history and realtime progress</p>
          </div>
          <div className="flex items-center gap-3">
          <label className="text-sm">
            <input
              checked={includeDeleted}
              type="checkbox"
              onChange={event => setIncludeDeleted(event.target.checked)}
            />{' '}
            Show deleted
          </label>
          <button className="v2-button v2-button-secondary" onClick={() => refresh()}>
            Refresh
          </button>
          </div>
        </div>
      </div>

      {error && <div className="rounded-xl bg-rose-100 p-3 text-rose-700 dark:bg-rose-950 dark:text-rose-200">{error}</div>}

      {loading ? (
        <p>Loading scans...</p>
      ) : scans.length === 0 ? (
        <div className="v2-card p-5 text-[var(--v2-text-muted)]">No scans found.</div>
      ) : (
        <div className="v2-card overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="bg-[var(--v2-bg)]">
              <tr>
                <th className="p-3">Name</th>
                <th className="p-3">Type</th>
                <th className="p-3">Tool</th>
                <th className="p-3">Status</th>
                <th className="p-3">Progress</th>
                <th className="p-3">Created</th>
                <th className="p-3">Actions</th>
              </tr>
            </thead>
            <tbody>
              {scans.map(scan => (
                <tr key={scan.id} className="border-t border-slate-200 dark:border-slate-800">
                  <td className="p-3 font-semibold">{scan.name}</td>
                  <td className="p-3">{scan.scan_type}</td>
                  <td className="p-3">{scan.tool_name || '—'}</td>
                  <td className="p-3">
                    <ScanStatusBadge status={scan.status} />
                  </td>
                  <td className="min-w-48 p-3">
                    <ScanProgressBar scan={scan} />
                  </td>
                  <td className="p-3">{new Date(scan.created_at).toLocaleString()}</td>
                  <td className="p-3">
                    <ScanActions
                      scan={scan}
                      onDelete={() => remove(scan)}
                      onInspect={() => setSelectedId(scan.id)}
                      onRename={() => rename(scan)}
                      onRunDemo={() => runDemo(scan)}
                      onRecommendations={() => { window.location.href = `/v2-recommendations?scan_id=${encodeURIComponent(scan.id)}`; }}
                      onParsedData={() => { window.location.href = `/v2-parsed-data?scan_id=${encodeURIComponent(scan.id)}`; }}
                      onStop={() => stop(scan)}
                    />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {selected && <ScanDetailsPanel scan={selected} onClose={() => setSelectedId(null)} onScanChange={replace} />}
    </div>
  );
}
