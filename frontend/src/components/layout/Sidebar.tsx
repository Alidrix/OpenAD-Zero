import {useEffect, useState, type ReactNode} from 'react';
import {NavLink, useParams} from 'react-router-dom';
import {ChevronDown, ChevronRight, Plus, Settings, Shield} from 'lucide-react';
import {getVersion, type VersionInfo} from '../../lib/api';

const link = 'block rounded-lg px-3 py-2 text-sm hover:bg-slate-100 dark:hover:bg-slate-800';
const active = ({isActive}: {isActive: boolean}) =>
  `${link} ${isActive ? 'bg-blue-100 font-semibold text-blue-800 dark:bg-blue-900/40 dark:text-blue-100' : ''}`;

function Section({title, children, initial = true}: {title: string; children: ReactNode; initial?: boolean}) {
  const [open, setOpen] = useState(initial);

  return (
    <div>
      <button
        className="flex w-full items-center justify-between rounded-lg px-2 py-2 text-left text-xs font-bold uppercase tracking-wide text-slate-500 hover:bg-slate-100 dark:hover:bg-slate-800"
        onClick={() => setOpen(!open)}
      >
        {title}
        {open ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
      </button>
      {open && <div className="ml-2 space-y-1 border-l border-slate-200 pl-2 dark:border-slate-800">{children}</div>}
    </div>
  );
}

export function Sidebar() {
  const {missionId} = useParams();
  const base = missionId ? `/missions/${missionId}` : '';
  const tool = (slug: string) => (missionId ? `${base}/tools/${slug}` : `/tools/${slug}`);
  const [version, setVersion] = useState<VersionInfo | null>(null);
  const [unavailable, setUnavailable] = useState(false);

  useEffect(() => {
    getVersion().then(setVersion).catch(() => setUnavailable(true));
  }, []);

  return (
    <aside className="sticky top-0 flex h-screen w-72 shrink-0 flex-col overflow-y-auto border-r border-slate-200 bg-white p-4 dark:border-[#1F2937] dark:bg-[#0F172A]">
      <div className="mb-6 flex items-center gap-2 text-xl font-bold">
        <Shield className="text-blue-500" />
        OpenAD Zero
      </div>

      <nav className="flex-1 space-y-2">
        <NavLink className={active} to="/missions/new">
          <Plus className="inline" size={16} /> Nouvelle mission
        </NavLink>
        {missionId && <NavLink className={active} to={base}>Dashboard</NavLink>}

        <Section title="V2 Operations">
          <NavLink className={active} to="/v2-attack-control">Attack Control Center</NavLink>
          <NavLink className={active} to="/v2-dashboard">V2 Dashboard</NavLink>
          <NavLink className={active} to="/scans">Scan Library</NavLink>
          <NavLink className={active} to="/v2-recommendations">V2 Recommendations</NavLink>
          <NavLink className={active} to="/v2-parsed-data">V2 Parsed Data</NavLink>
          <NavLink className={active} to="/v2-brand">V2 Brand</NavLink>
        </Section>

        <Section title="Scope & Setup">
          <NavLink className={active} to={missionId ? `${base}/lab` : '/missions/new'}>Scope validation</NavLink>
          <NavLink className={active} to={missionId ? `${base}/hosts` : '/missions/new'}>Targets</NavLink>
          <NavLink className={active} to={missionId ? `${base}/actions` : '/missions/new'}>Credentials</NavLink>
          <NavLink className={active} to={missionId ? `${base}/evidence` : '/missions/new'}>Artifacts</NavLink>
        </Section>

        <Section title="Recon">
          <NavLink className={active} to={tool('nmap')}>Nmap</NavLink>
          <NavLink className={active} to={tool('nuclei')}>Nuclei</NavLink>
          <NavLink className={active} to={tool('enum4linux')}>enum4linux-ng</NavLink>
        </Section>

        <Section title="SMB / NetExec">
          <NavLink className={active} to={tool('netexec')}>SMB fingerprint</NavLink>
          <NavLink className={active} to={tool('netexec')}>SMB signing check</NavLink>
          <NavLink className={active} to={tool('netexec')}>Null session check</NavLink>
          <NavLink className={active} to={tool('netexec')}>Shares</NavLink>
        </Section>

        <Section title="Active Directory">
          <NavLink className={active} to={tool('kerbrute')}>Kerbrute</NavLink>
          <NavLink className={active} to={tool('gmsadumper')}>gMSADumper</NavLink>
          <NavLink className={active} to={tool('bloodyad')}>BloodyAD</NavLink>
          <NavLink className={active} to={missionId ? `${base}/bloodhound` : '/tools/bloodhound'}>BloodHound</NavLink>
        </Section>

        <Section title="Coercion / Capture">
          <NavLink className={active} to={tool('coercer')}>Coercer</NavLink>
          <NavLink className={active} to={tool('responder')}>Responder</NavLink>
        </Section>

        <Section title="Impacket">
          <NavLink className={active} to={tool('impacket')}>GetNPUsers</NavLink>
          <NavLink className={active} to={tool('impacket')}>GetUserSPNs</NavLink>
          <NavLink className={active} to={tool('impacket')}>LookupSID</NavLink>
          <NavLink className={active} to={tool('impacket')}>SMB client</NavLink>
          <NavLink className={active} to={tool('impacket')}>RPC dump</NavLink>
          <NavLink className={active} to={tool('impacket')}>SAMR dump</NavLink>
        </Section>

        <Section title="Exploit Research">
          <NavLink className={active} to={tool('metasploit')}>Metasploit search</NavLink>
          <NavLink className={active} to={tool('metasploit')}>Suggested searches</NavLink>
          <NavLink className={active} to={tool('metasploit')}>CVE correlation</NavLink>
        </Section>

        <Section title="Credentials Review">
          <NavLink className={active} to={tool('donpapi')}>DonPAPI</NavLink>
          <NavLink className={active} to={missionId ? `${base}/evidence` : '/missions/new'}>Evidence import</NavLink>
          <NavLink className={active} to={missionId ? `${base}/findings` : '/missions/new'}>Findings</NavLink>
        </Section>

        <Section title="Reports">
          <NavLink className={active} to={missionId ? `${base}/evidence` : '/missions/new'}>Evidence</NavLink>
          <NavLink className={active} to={missionId ? `${base}/report` : '/missions/new'}>Export</NavLink>
          <NavLink className={active} to="/settings">Release readiness</NavLink>
        </Section>

        <Section title="Settings">
          <NavLink className={active} to="/capabilities">Capabilities</NavLink>
          <NavLink className={active} to="/tools/nmap">Tool automation</NavLink>
          <NavLink className={active} to="/settings"><Settings className="inline" size={16} /> Governance</NavLink>
        </Section>
      </nav>

      <div className="mt-6 border-t border-slate-200 pt-4 text-xs text-slate-500 dark:border-slate-800">
        <div className="font-semibold text-slate-700 dark:text-slate-300">{version?.name || 'OpenAD Zero'}</div>
        {version ? <><div>v{version.version}</div><div>{version.release_stage}</div></> : <div>{unavailable ? 'Version unavailable' : 'Loading version...'}</div>}
      </div>
    </aside>
  );
}
