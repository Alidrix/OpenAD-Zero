import {useCallback, useEffect, useState} from 'react';
import {useSearchParams} from 'react-router-dom';
import {
  listParseDiagnostics,
  listParsedAssets,
  listParsedServices,
  listParsedSignals,
  parsePersistedScan,
  type ParseDiagnostic,
  type ParsedAsset,
  type ParsedService,
  type ParsedSignal,
  type ParsePersistedResult,
} from '../lib/v2ParsingApi';
import {listScans, type V2Scan} from '../lib/v2ScansApi';
import '../styles/v2-theme.css';

function Panel({title, rows}: {title: string; rows: string[]}) {
  return (
    <div className="v2-card p-5">
      <h2 className="text-xl font-semibold">{title}</h2>
      {rows.length === 0 ? (
        <p className="mt-3 text-sm text-slate-500">No rows.</p>
      ) : (
        <div className="mt-3 max-h-80 space-y-2 overflow-auto">
          {rows.map((row, index) => (
            <div className="rounded-xl bg-slate-50 p-3 text-sm dark:bg-slate-800" key={`${row}-${index}`}>
              {row}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export function V2ParsedDataPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [scans, setScans] = useState<V2Scan[]>([]);
  const [selectedScanId, setSelectedScanId] = useState(searchParams.get('scan_id') || '');
  const [assets, setAssets] = useState<ParsedAsset[]>([]);
  const [services, setServices] = useState<ParsedService[]>([]);
  const [signals, setSignals] = useState<ParsedSignal[]>([]);
  const [diagnostics, setDiagnostics] = useState<ParseDiagnostic[]>([]);
  const [result, setResult] = useState<ParsePersistedResult | null>(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const refresh = useCallback(async (scanId = selectedScanId) => {
    if (!scanId) {
      setAssets([]);
      setServices([]);
      setSignals([]);
      setDiagnostics([]);
      return;
    }

    const [nextAssets, nextServices, nextSignals, nextDiagnostics] = await Promise.all([
      listParsedAssets(scanId),
      listParsedServices(scanId),
      listParsedSignals(scanId),
      listParseDiagnostics(scanId),
    ]);

    setAssets(nextAssets);
    setServices(nextServices);
    setSignals(nextSignals);
    setDiagnostics(nextDiagnostics);
  }, [selectedScanId]);

  useEffect(() => {
    const queryScanId = searchParams.get('scan_id') || '';

    listScans(false)
      .then(rows => {
        setScans(rows);

        if (!queryScanId) {
          return;
        }

        if (!rows.some(scan => scan.id === queryScanId)) {
          setError(`Scan ${queryScanId} was not found in the scan library.`);
          return;
        }

        setSelectedScanId(queryScanId);
        refresh(queryScanId).catch(err => setError(String(err)));
      })
      .catch(err => setError(String(err)));
  }, [refresh, searchParams]);

  function chooseScan(scanId: string) {
    setSelectedScanId(scanId);
    setSearchParams(scanId ? {scan_id: scanId} : {});
    setResult(null);
    setError('');
    refresh(scanId).catch(err => setError(String(err)));
  }

  async function parseSelected() {
    if (!selectedScanId) {
      return;
    }

    setLoading(true);
    setError('');
    try {
      const parseResult = await parsePersistedScan(selectedScanId);
      setResult(parseResult);
      await refresh(selectedScanId);
    } catch (err) {
      setError(String(err));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="v2-shell space-y-6">
      <section className="v2-card p-6">
        <h1 className="text-3xl font-bold">V2 Parsed Data</h1>
        <p className="text-[var(--v2-text-muted)]">
          Normalized scan assets, services, signals, and diagnostics persisted in PostgreSQL.
        </p>
      </section>

      <section className="v2-card grid gap-3 p-5 md:grid-cols-4">
        <span className="v2-badge">Parsing persisted data only</span>
        <span className="v2-badge">No external tool execution</span>
        <span className="v2-badge">No subprocess</span>
        <span className="v2-badge">PostgreSQL is the source of truth</span>
      </section>

      {error && <div className="rounded-xl bg-rose-100 p-3 text-rose-700 dark:bg-rose-950 dark:text-rose-200">{error}</div>}

      <section className="v2-card p-5">
        <h2 className="text-xl font-semibold">Scan selector</h2>
        <select
          className="mt-3 w-full rounded-lg border border-slate-300 bg-transparent p-2"
          value={selectedScanId}
          onChange={event => chooseScan(event.target.value)}
        >
          <option value="">Select a scan</option>
          {scans.map(scan => (
            <option key={scan.id} value={scan.id}>
              {scan.name} · {scan.status}
            </option>
          ))}
        </select>
        <div className="mt-3 flex flex-wrap gap-2">
          <button className="v2-button" disabled={!selectedScanId || loading} onClick={parseSelected}>
            Parse persisted data
          </button>
          <button
            className="v2-button v2-button-secondary"
            disabled={!selectedScanId || loading}
            onClick={() => refresh().catch(err => setError(String(err)))}
          >
            Refresh parsed data
          </button>
        </div>
        {result && (
          <p className="mt-3 text-sm text-slate-500">
            Parsed {result.assets_created} assets, {result.services_created} services, {result.signals_created} signals,
            {' '}{result.diagnostics_created} diagnostics.
          </p>
        )}
      </section>

      <section className="grid gap-6 xl:grid-cols-2">
        <Panel
          title="Parsed assets"
          rows={assets.map(asset => `${asset.ip_address}${asset.hostname ? ` · ${asset.hostname}` : ''}${asset.os_name ? ` · ${asset.os_name}` : ''}`)}
        />
        <Panel
          title="Parsed services"
          rows={services.map(service => `${service.ip_address}:${service.port}/${service.protocol} · ${service.service_name || 'unknown'} · ${service.state}`)}
        />
        <Panel
          title="Parsed signals"
          rows={signals.map(signal => `${signal.signal} · ${signal.value} · confidence ${signal.confidence}`)}
        />
        <Panel
          title="Diagnostics"
          rows={diagnostics.map(diagnostic => `${diagnostic.level}: ${diagnostic.message}`)}
        />
      </section>
    </div>
  );
}
