import {useCallback,useState} from 'react';
import type {ToastMessage} from '../components/ui/Toast';

export function useToasts(){
  const [toasts,setToasts]=useState<ToastMessage[]>([]);
  const push=useCallback((type:ToastMessage['type'],message:string)=>{const id=Date.now()+Math.random();setToasts(t=>[...t,{id,type,message}]);window.setTimeout(()=>setToasts(t=>t.filter(x=>x.id!==id)),5000)},[]);
  const dismiss=useCallback((id:number)=>setToasts(t=>t.filter(x=>x.id!==id)),[]);
  return {toasts,dismiss,success:(m:string)=>push('success',m),error:(m:string)=>push('error',m),info:(m:string)=>push('info',m)};
}
