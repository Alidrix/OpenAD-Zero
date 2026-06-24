import {RiskBadge} from './RiskBadge';export function GraphEdgeLabel({edge}:any){return <span>{edge?.edge_type||edge?.label} <RiskBadge risk={edge?.risk}/></span>}
