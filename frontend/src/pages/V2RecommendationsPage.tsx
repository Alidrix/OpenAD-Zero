import {useCallback, useEffect, useMemo, useState} from 'react';
import {useSearchParams} from 'react-router-dom';
import {
  buildCommandPreview,
  getRecommendationCatalog,
  getScanRecommendations,
  type V2CommandPreview,
  type V2Recommendation,
  type V2SafeTemplate,
} from '../lib/v2RecommendationsApi';
import {listScans, type V2Scan} from '../lib/v2ScansApi';
import '../styles/v2-theme.css';

function Badge({children}: {children: string}) {
  return (
    <span className="v2-badge bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-200">
      {children}
    </span>
  );
}

function formatPreview(preview: V2CommandPreview): string {
  return preview.argv_preview.join(' ');
}

export function V2RecommendationsPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [templates, setTemplates] = useState<V2SafeTemplate[]>([]);
  const [scans, setScans] = useState<V2Scan[]>([]);
  const [selectedScanId, setSelectedScanId] = useState(
    searchParams.get('scan_id') || '',
  );
  const [recommendations, setRecommendations] = useState<V2Recommendation[]>([]);
  const [selectedTemplateId, setSelectedTemplateId] = useState('');
  const [params, setParams] = useState<Record<string, string>>({});
  const [preview, setPreview] = useState<V2CommandPreview | null>(null);
  const [error, setError] = useState('');

  const selectedTemplate = useMemo(
    () => templates.find(template => template.id === selectedTemplateId),
    [templates, selectedTemplateId],
  );
  const requiredInputs = selectedTemplate?.expected_inputs || [];

  const refreshRecommendations = useCallback(
    async (scanId = selectedScanId) => {
      if (!scanId) {
        setRecommendations([]);
        return;
      }

      const rows = await getScanRecommendations(scanId);
      setRecommendations(rows);

      if (!selectedTemplateId && rows[0]) {
        setSelectedTemplateId(rows[0].template_id);
      }
    },
    [selectedScanId, selectedTemplateId],
  );

  const loadPageData = useCallback(async () => {
    setError('');

    const [catalog, scanRows] = await Promise.all([
      getRecommendationCatalog(),
      listScans(false),
    ]);

    setTemplates(catalog.templates);
    setScans(scanRows);

    const queryScanId = searchParams.get('scan_id') || '';
    if (!queryScanId) {
      return;
    }

    const scanExists = scanRows.some(scan => scan.id === queryScanId);
    if (!scanExists) {
      setRecommendations([]);
      setError(`Scan ${queryScanId} was not found in the scan library.`);
      return;
    }

    setSelectedScanId(queryScanId);
    await refreshRecommendations(queryScanId);
  }, [refreshRecommendations, searchParams]);

  useEffect(() => {
    loadPageData().catch(err => setError(String(err)));
  }, [loadPageData]);

  function chooseScan(scanId: string) {
    setSelectedScanId(scanId);
    setSearchParams(scanId ? {scan_id: scanId} : {});
    setPreview(null);
  }

  function chooseTemplate(templateId: string) {
    setSelectedTemplateId(templateId);
    setPreview(null);
    setParams({});
  }

  async function onBuildPreview() {
    if (!selectedTemplateId) {
      return;
    }

    setError('');
    setPreview(await buildCommandPreview(selectedTemplateId, params));
  }

  return (
    <div className="v2-shell space-y-6">
      <section className="v2-card p-6">
        <h1 className="text-3xl font-bold">V2 Recommendations</h1>
        <p className="text-[var(--v2-text-muted)]">
          Safe-by-default template suggestions and command previews
        </p>
      </section>

      <section className="v2-card grid gap-3 p-5 md:grid-cols-4">
        <Badge>Preview only</Badge>
        <Badge>No automatic execution</Badge>
        <Badge>No raw frontend commands</Badge>
        <Badge>Backend rebuilds argv from allowlisted templates</Badge>
      </section>

      {error && (
        <div className="rounded-xl bg-rose-100 p-3 text-rose-700 dark:bg-rose-950 dark:text-rose-200">
          {error}
        </div>
      )}

      <section className="grid gap-6 xl:grid-cols-2">
        <div className="v2-card p-5">
          <h2 className="text-xl font-semibold">Catalog</h2>
          <div className="mt-4 max-h-[34rem] space-y-3 overflow-auto">
            {templates.map(template => (
              <button
                className="w-full rounded-xl border border-slate-200 p-3 text-left hover:bg-slate-50 dark:border-slate-800 dark:hover:bg-slate-800"
                key={template.id}
                onClick={() => chooseTemplate(template.id)}
              >
                <div className="font-semibold">{template.name}</div>
                <p className="text-sm text-slate-500">{template.description}</p>
                <div className="mt-2 flex flex-wrap gap-2 text-xs">
                  <Badge>{template.category}</Badge>
                  <Badge>{template.risk_level}</Badge>
                  <Badge>{template.mode}</Badge>
                </div>
                <p className="mt-2 text-xs text-slate-500">
                  Required inputs: {template.expected_inputs.join(', ') || 'none'}
                </p>
              </button>
            ))}
          </div>
        </div>

        <div className="v2-card p-5">
          <h2 className="text-xl font-semibold">Scan recommendations</h2>
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
          <button
            className="v2-button v2-button-secondary mt-3"
            onClick={() => refreshRecommendations().catch(err => setError(String(err)))}
          >
            Refresh recommendations
          </button>
          <div className="mt-4 space-y-3">
            {recommendations.length === 0 ? (
              <p className="text-sm text-slate-500">
                No scan-specific recommendations yet.
              </p>
            ) : (
              recommendations.map(rec => (
                <button
                  className="w-full rounded-xl border border-slate-200 p-3 text-left hover:bg-slate-50 dark:border-slate-800 dark:hover:bg-slate-800"
                  key={rec.recommendation_id}
                  onClick={() => chooseTemplate(rec.template_id)}
                >
                  <div className="font-semibold">{rec.name}</div>
                  <p className="text-sm">{rec.reason}</p>
                  <div className="mt-2 flex flex-wrap gap-2 text-xs">
                    <Badge>{rec.priority}</Badge>
                    <Badge>{rec.risk_level}</Badge>
                    <Badge>{rec.mode}</Badge>
                  </div>
                </button>
              ))
            )}
          </div>
        </div>
      </section>

      <section className="v2-card p-5">
        <h2 className="text-xl font-semibold">Command Preview</h2>
        <p className="text-sm text-slate-500">
          Choose a recommendation or catalog item, fill required parameters, then
          build a backend-rendered read-only preview.
        </p>
        <select
          className="mt-3 w-full rounded-lg border border-slate-300 bg-transparent p-2"
          value={selectedTemplateId}
          onChange={event => chooseTemplate(event.target.value)}
        >
          <option value="">Select a template</option>
          {templates.map(template => (
            <option key={template.id} value={template.id}>
              {template.name}
            </option>
          ))}
        </select>
        <div className="mt-4 grid gap-3 md:grid-cols-2">
          {requiredInputs.map(input => (
            <label className="text-sm font-medium" key={input}>
              {input}
              <input
                className="mt-1 w-full rounded-lg border border-slate-300 bg-transparent p-2"
                value={params[input] || ''}
                onChange={event =>
                  setParams(old => ({...old, [input]: event.target.value}))
                }
              />
            </label>
          ))}
        </div>
        <button
          className="v2-button mt-4"
          disabled={!selectedTemplateId}
          onClick={() => onBuildPreview().catch(err => setError(String(err)))}
        >
          Build preview
        </button>
        {preview && (
          <div className="mt-4 space-y-3">
            <pre className="overflow-auto rounded-xl bg-slate-950 p-4 text-sm text-slate-100">
              {formatPreview(preview)}
            </pre>
            <p className="text-sm">
              executable: {String(preview.executable)} ·
              automatic_execution_allowed:{' '}
              {String(preview.automatic_execution_allowed)}
            </p>
            {preview.missing_params.length > 0 && (
              <p className="text-sm text-amber-600">
                Missing params: {preview.missing_params.join(', ')}
              </p>
            )}
            <button
              className="v2-button v2-button-secondary"
              onClick={() => navigator.clipboard?.writeText(formatPreview(preview))}
            >
              Copy preview text
            </button>
            <ul className="list-disc pl-5 text-sm text-slate-500">
              {preview.safety_notes.map(note => (
                <li key={note}>{note}</li>
              ))}
            </ul>
          </div>
        )}
      </section>
    </div>
  );
}
