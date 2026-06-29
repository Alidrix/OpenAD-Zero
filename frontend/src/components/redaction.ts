export const MASK='********';
const sensitiveName=/(password|pass|pwd|hash|ntlm|token|secret|key|api[_-]?key|authorization|cookie|session|SMBPass|SMBUser)/i;
const assignment=/\b(password|pass|pwd|hash|ntlm(?:_hash)?|token|secret|key|api[_-]?key|authorization|cookie|session|SMBPass|SMBUser)\b(\s*[:=]\s*)([^\s,;]+)/gi;
const ntlm=/\b[a-f0-9]{32}(?::[a-f0-9]{32})?\b/gi;
const kerberos=/\$krb5(?:asrep|tgs)\$[^\s]+/gi;
export function isSensitiveName(name:string){return sensitiveName.test(name)}
export function redactText(text:string){return text.replace(assignment,`$1$2${MASK}`).replace(kerberos,MASK).replace(ntlm,MASK).replace(/\b(Bearer|Basic)\s+[^\s,;]+/gi,`$1 ${MASK}`)}
export function redactValue(value:any):any{if(typeof value==='string')return redactText(value);if(Array.isArray(value))return value.map(redactValue);if(value&&typeof value==='object')return Object.fromEntries(Object.entries(value).map(([k,v])=>[k,isSensitiveName(k)?MASK:redactValue(v)]));return value}
