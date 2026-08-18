import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import Layout from '@/components/Layout';
import { AppProvider } from '@/context/AppContext';
import Dashboard from '@/pages/Dashboard';
import SafetyMap from '@/pages/SafetyMap';
import SafeRoute from '@/pages/SafeRoute';
import Journey from '@/pages/Journey';
import SafeHavens from '@/pages/SafeHavens';
import Incidents from '@/pages/Incidents';
import Community from '@/pages/Community';
import Emergency from '@/pages/Emergency';
import Settings from '@/pages/Settings';

export default function App() {
  return (
    <AppProvider>
      <BrowserRouter>
        <Layout>
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/safety-map" element={<SafetyMap />} />
            <Route path="/safe-route" element={<SafeRoute />} />
            <Route path="/journey" element={<Journey />} />
            <Route path="/safe-havens" element={<SafeHavens />} />
            <Route path="/incidents" element={<Incidents />} />
            <Route path="/community" element={<Community />} />
            <Route path="/emergency" element={<Emergency />} />
            <Route path="/settings" element={<Settings />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </Layout>
      </BrowserRouter>
    </AppProvider>
  );
}
