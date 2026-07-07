import {severityStyles} from '../../lib/designSystem';
export function SeverityBadge({severity}:{severity?:string}){const s=(severity||'info').toLowerCase();return <span className={`inline-flex rounded-full px-2.5 py-1 text-xs font-semibold ring-1 ${severityStyles[s]||severityStyles.info}`}>{s}</span>}
