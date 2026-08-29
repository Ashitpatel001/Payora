import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { Sidebar } from './components/Sidebar';
import { TopBar } from './components/TopBar';
import { Dashboard } from './pages/Dashboard';
import { Queue } from './pages/Queue';
import { CaseDetail } from './pages/CaseDetail';
import { GuardrailLog } from './pages/GuardrailLog';
import { BatchMetrics } from './pages/BatchMetrics';

export default function App() {
  return (
    <Router>
      <div className="min-h-screen bg-page text-text-primary flex">
        {/* Fixed Left Navigation Sidebar */}
        <Sidebar />

        {/* Main Content Shell with Sticky TopBar */}
        <div className="flex-1 flex flex-col min-w-0 ml-64">
          <TopBar />
          <main className="flex-1 pb-16">
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/dashboard" element={<Dashboard />} />
              <Route path="/queue" element={<Queue />} />
              <Route path="/cases/:id" element={<CaseDetail />} />
              <Route path="/guardrails" element={<GuardrailLog />} />
              <Route path="/metrics" element={<BatchMetrics />} />
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </main>
        </div>
      </div>
    </Router>
  );
}
