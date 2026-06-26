DEFAULT_PHASES = [
    {
        'phase_key': 'scope_validation',
        'name': 'Scope validation',
        'description': 'Mission scope is validated and locked.',
        'order_index': 1,
    },
    {
        'phase_key': 'network_discovery',
        'name': 'Network discovery',
        'description': 'Nmap discovers hosts and services.',
        'order_index': 2,
    },
    {
        'phase_key': 'service_enumeration',
        'name': 'Service enumeration',
        'description': 'Detected services are classified.',
        'order_index': 3,
    },
    {
        'phase_key': 'smb_enrichment',
        'name': 'SMB enrichment',
        'description': 'NetExec enriches Windows/SMB exposure.',
        'order_index': 4,
    },
    {
        'phase_key': 'web_exposure_scan',
        'name': 'Web exposure scan',
        'description': 'Nuclei checks HTTP/HTTPS targets.',
        'order_index': 5,
    },
    {
        'phase_key': 'active_directory_collection',
        'name': 'Active Directory graph collection',
        'description': 'SharpHound/BloodHound data is imported.',
        'order_index': 6,
    },
    {
        'phase_key': 'bloodhound_analysis',
        'name': 'BloodHound analysis',
        'description': 'AD objects, relations and permissions are analyzed.',
        'order_index': 7,
    },
    {
        'phase_key': 'pathfinding',
        'name': 'Pathfinding',
        'description': 'Paths to sensitive groups are analyzed.',
        'order_index': 8,
    },
    {
        'phase_key': 'evidence_consolidation',
        'name': 'Evidence consolidation',
        'description': 'Evidence is imported and linked.',
        'order_index': 9,
    },
    {
        'phase_key': 'reporting',
        'name': 'Reporting',
        'description': 'Markdown/HTML reports are generated.',
        'order_index': 10,
    },
]
PHASE_STATUSES = {'pending', 'running', 'completed', 'blocked', 'skipped', 'failed'}
OBJECTIVE_TYPES = {
    'domain_admin_path',
    'critical_asset_access',
    'credential_exposure_validation',
    'lateral_movement_validation',
    'custom',
}
OBJECTIVE_STATUSES = {'not_started', 'in_progress', 'evidence_collected', 'validated', 'blocked', 'not_applicable'}
TIMELINE_SOURCES = {'system', 'nmap', 'netexec', 'nuclei', 'bloodhound', 'evidence', 'report', 'planner', 'manual'}
TIMELINE_SEVERITIES = {'info', 'low', 'medium', 'high', 'critical', 'success', 'warning', 'error'}
