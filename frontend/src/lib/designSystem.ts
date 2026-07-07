export const colors = {
  ink: '#0f172a', muted: '#64748b', panel: '#ffffff', canvas: '#f7f9fc', border: '#e2e8f0',
  violet: '#7c3aed', cyan: '#06b6d4', success: '#16a34a', warning: '#d97706', danger: '#dc2626', rose: '#e11d48', blue: '#2563eb',
};

export const gradients = {
  sidebar: 'bg-gradient-to-b from-slate-950 via-indigo-950 to-slate-900',
  hero: 'bg-[radial-gradient(circle_at_top_left,rgba(124,58,237,0.14),transparent_34%),radial-gradient(circle_at_top_right,rgba(6,182,212,0.12),transparent_30%)]',
  accent: 'bg-gradient-to-r from-violet-600 to-cyan-500',
};

export const shadows = {card: 'shadow-sm shadow-slate-200/70', elevated: 'shadow-2xl shadow-slate-900/20'};
export const radius = {card: 'rounded-2xl', pill: 'rounded-full', modal: 'rounded-3xl'};
export const spacing = {page: 'p-4 sm:p-6 lg:p-8', section: 'space-y-6'};

export const motionPresets = {
  page: {initial: {opacity: 0, y: 10}, animate: {opacity: 1, y: 0}, transition: {duration: 0.22}},
  card: (i = 0) => ({initial: {opacity: 0, y: 12}, animate: {opacity: 1, y: 0}, transition: {duration: 0.2, delay: i * 0.035}}),
  press: {whileHover: {y: -1}, whileTap: {scale: 0.98}},
};

export const severityStyles: Record<string, string> = {
  critical: 'bg-red-50 text-red-700 ring-red-200', high: 'bg-rose-50 text-rose-700 ring-rose-200', medium: 'bg-orange-50 text-orange-700 ring-orange-200', low: 'bg-blue-50 text-blue-700 ring-blue-200', info: 'bg-slate-50 text-slate-700 ring-slate-200',
};
export const riskStyles = severityStyles;
export const phaseStatusStyles: Record<string, string> = {
  not_started: 'bg-slate-50 text-slate-600 ring-slate-200', ready: 'bg-blue-50 text-blue-700 ring-blue-200', running: 'bg-cyan-50 text-cyan-700 ring-cyan-200', waiting_approval: 'bg-amber-50 text-amber-700 ring-amber-200', completed: 'bg-emerald-50 text-emerald-700 ring-emerald-200', blocked: 'bg-slate-100 text-slate-700 ring-slate-300', failed: 'bg-red-50 text-red-700 ring-red-200', skipped: 'bg-zinc-50 text-zinc-600 ring-zinc-200', proposed: 'bg-violet-50 text-violet-700 ring-violet-200', approved: 'bg-emerald-50 text-emerald-700 ring-emerald-200', rejected: 'bg-red-50 text-red-700 ring-red-200', queued: 'bg-indigo-50 text-indigo-700 ring-indigo-200',
};
export const executionModeStyles: Record<string, string> = {
  safe_auto: 'bg-emerald-50 text-emerald-700 ring-emerald-200', approval_required: 'bg-amber-50 text-amber-700 ring-amber-200', reinforced_approval_required: 'bg-rose-50 text-rose-700 ring-rose-200', manual_only: 'bg-slate-100 text-slate-700 ring-slate-300',
};
