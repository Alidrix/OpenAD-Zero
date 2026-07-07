import {executionModeStyles} from '../../lib/designSystem';
export function ExecutionModeBadge({mode}:{mode?:string}){const m=mode||'manual_only';return <span className={`inline-flex rounded-full px-2.5 py-1 text-xs font-semibold ring-1 ${executionModeStyles[m]||executionModeStyles.manual_only}`}>{m.replace(/_/g,' ')}</span>}
