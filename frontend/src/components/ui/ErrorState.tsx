export function ErrorState({title='Unable to load data',error}:{title?:string;error?:unknown}){
  const message = error instanceof Error ? error.message : error ? String(error) : '';
  return <div className='rounded-xl border border-red-500/40 bg-red-500/10 p-4'><h3 className='font-semibold text-red-100'>{title}</h3>{message&&<p className='mt-1 text-sm text-red-200'>{message}</p>}</div>
}
