import {phaseStatusStyles} from '../../lib/designSystem';
export function StatusBadge({status}:{status?:string}){const s=status||'unknown';return <span className={`inline-flex rounded-full px-2.5 py-1 text-xs font-semibold ring-1 ${phaseStatusStyles[s]||phaseStatusStyles.not_started}`}>{s.replace(/_/g,' ')}</span>}
