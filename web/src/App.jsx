import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './useAuth';
import Layout from './components/Layout';
import DashboardLayout from './components/DashboardLayout';
import Landing from './pages/Landing';
import Catalogue from './pages/Catalogue';
import ProductDetail from './pages/ProductDetail';
import Login from './pages/Login';
import Register from './pages/Register';
import RegisterAgent from './pages/RegisterAgent';
import AdminDashboard from './pages/dashboard/AdminDashboard';
import ManufacturerDashboard from './pages/dashboard/ManufacturerDashboard';
import TeamDashboard from './pages/dashboard/TeamDashboard';
import AgentDashboard from './pages/dashboard/AgentDashboard';

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route element={<Layout />}>
            <Route path="/" element={<Landing />} />
            <Route path="/catalogue" element={<Catalogue />} />
            <Route path="/product/:id" element={<ProductDetail />} />
            <Route path="/login" element={<Login />} />
            <Route path="/register" element={<Register />} />
            <Route path="/register/agent" element={<RegisterAgent />} />
          </Route>
          <Route element={<DashboardLayout />}>
            <Route path="/dashboard/admin" element={<AdminDashboard />} />
            <Route path="/dashboard/manufacturer" element={<ManufacturerDashboard />} />
            <Route path="/dashboard/team" element={<TeamDashboard />} />
            <Route path="/dashboard/agent" element={<AgentDashboard />} />
          </Route>
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}
