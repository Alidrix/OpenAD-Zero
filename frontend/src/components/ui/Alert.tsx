import type {ReactNode} from 'react';

export function Alert({children,tone='info'}:{children:ReactNode;tone?:'info'|'success'|'warning'|'danger'}){
  const tones={info:'border-blue-500/40 bg-blue-500/10 text-blue-100',success:'border-emerald-500/40 bg-emerald-500/10 text-emerald-100',warning:'border-amber-500/40 bg-amber-500/10 text-amber-100',danger:'border-red-500/40 bg-red-500/10 text-red-100'};
  return <div className={`rounded-lg border px-4 py-3 text-sm ${tones[tone]}`}>{children}</div>;
}
