import {Navigate, Route, Routes} from 'react-router-dom';
import {AppLayout} from './components/layout/AppLayout';
import {ActionsPage} from './pages/ActionsPage';
import {CapabilitiesPage} from './pages/CapabilitiesPage';
import {EvidencePage} from './pages/EvidencePage';
import {FindingsPage} from './pages/FindingsPage';
import {HostsPage} from './pages/HostsPage';
import {JobsPage} from './pages/JobsPage';
import {LabOperationsPage} from './pages/LabOperationsPage';
import {MissionDashboardPage} from './pages/MissionDashboardPage';
import {NewMissionPage} from './pages/NewMissionPage';
import {ReportPage} from './pages/ReportPage';
import {ScanLibrary} from './pages/ScanLibrary';
import {SettingsPage} from './pages/SettingsPage';
import {TimelinePage} from './pages/TimelinePage';
import {ToolConsolePage} from './pages/ToolConsolePage';
import {V2DashboardPage} from './pages/V2DashboardPage';
import {WebTargetsPage} from './pages/WebTargetsPage';
import {BloodHoundExplorerPage} from './pages/bloodhound/BloodHoundExplorerPage';
import {BloodHoundPage} from './pages/bloodhound/BloodHoundPage';

export default function App() {
  return (
    <Routes>
      <Route element={<AppLayout />}>
        <Route path="/" element={<Navigate to="/missions/new" />} />
        <Route path="/missions/new" element={<NewMissionPage />} />
        <Route path="/missions/:missionId" element={<MissionDashboardPage />} />
        <Route path="/missions/:missionId/hosts" element={<HostsPage />} />
        <Route path="/missions/:missionId/actions" element={<ActionsPage />} />
        <Route path="/missions/:missionId/jobs" element={<JobsPage />} />
        <Route path="/missions/:missionId/web" element={<WebTargetsPage />} />
        <Route path="/missions/:missionId/findings" element={<FindingsPage />} />
        <Route path="/missions/:missionId/evidence" element={<EvidencePage />} />
        <Route path="/missions/:missionId/report" element={<ReportPage />} />
        <Route path="/missions/:missionId/lab" element={<LabOperationsPage />} />
        <Route path="/missions/:missionId/timeline" element={<TimelinePage />} />
        <Route path="/missions/:missionId/bloodhound" element={<BloodHoundPage />} />
        <Route path="/missions/:missionId/bloodhound/explorer" element={<BloodHoundExplorerPage />} />
        <Route path="/findings" element={<FindingsPage />} />
        <Route path="/capabilities" element={<CapabilitiesPage />} />
        <Route path="/settings" element={<SettingsPage />} />
        <Route path="/scans" element={<ScanLibrary />} />
        <Route path="/v2-dashboard" element={<V2DashboardPage />} />
        <Route path="/tools/:toolSlug" element={<ToolConsolePage />} />
        <Route path="/missions/:missionId/tools/:toolSlug" element={<ToolConsolePage />} />
      </Route>
    </Routes>
  );
}
