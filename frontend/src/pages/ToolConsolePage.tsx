import {useParams} from 'react-router-dom';import {ToolConsole} from '../components/ToolConsole';
export function ToolConsolePage(){const {toolSlug='nmap'}=useParams();return <ToolConsole toolSlug={toolSlug}/>}
