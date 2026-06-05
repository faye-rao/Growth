import { Routes, Route, Navigate } from "react-router-dom";
import AppLayout from "./layout/AppLayout";
import AudiencePage from "./features/audience/AudiencePage";
import CampaignPage from "./features/campaign/CampaignPage";
import AnalyticsPage from "./features/analytics/AnalyticsPage";
import PersonalizationPage from "./features/personalization/PersonalizationPage";
import ContentPage from "./features/content/ContentPage";
import ExperimentPage from "./features/experiment/ExperimentPage";
import DataPage from "./features/data/DataPage";

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<AppLayout />}>
        <Route index element={<Navigate to="/audience" replace />} />
        <Route path="audience" element={<AudiencePage />} />
        <Route path="campaign" element={<CampaignPage />} />
        <Route path="analytics" element={<AnalyticsPage />} />
        <Route path="personalization" element={<PersonalizationPage />} />
        <Route path="content" element={<ContentPage />} />
        <Route path="experiment" element={<ExperimentPage />} />
        <Route path="data" element={<DataPage />} />
        <Route path="*" element={<Navigate to="/audience" replace />} />
      </Route>
    </Routes>
  );
}
