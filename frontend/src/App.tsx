import { Routes, Route, Navigate } from "react-router-dom";
import AppLayout from "./layout/AppLayout";
import Placeholder from "./pages/Placeholder";
import AudiencePage from "./features/audience/AudiencePage";
import CampaignPage from "./features/campaign/CampaignPage";

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<AppLayout />}>
        <Route index element={<Navigate to="/audience" replace />} />
        <Route path="audience" element={<AudiencePage />} />
        <Route path="campaign" element={<CampaignPage />} />
        <Route path="analytics" element={<Placeholder title="Analytics (M4+M9)" />} />
        <Route path="personalization" element={<Placeholder title="Personalization (M5)" />} />
        <Route path="content" element={<Placeholder title="Content (M6)" />} />
        <Route path="experiment" element={<Placeholder title="Experiment (M7)" />} />
        <Route path="data" element={<Placeholder title="Data Platform (M8)" />} />
        <Route path="*" element={<Navigate to="/audience" replace />} />
      </Route>
    </Routes>
  );
}
