import { Navigate, Outlet, Link } from 'react-router-dom';
import { useAuth } from '../useAuth';

const ROLE_PATH = { super_admin: 'admin', manufacturer: 'manufacturer', team_member: 'team', agent: 'agent' };

export default function DashboardLayout() {
  const { user, logout, loading } = useAuth();

  if (loading) return <div className="p-10 text-center text-gray-500">Loading...</div>;
  if (!user) return <Navigate to="/login" replace />;

  const role = user.role;
  const path = ROLE_PATH[role] || 'agent';

  const links = {
    admin: [
      { to: '/dashboard/admin', label: 'Overview' },
    ],
    manufacturer: [
      { to: '/dashboard/manufacturer', label: 'Pending Orders' },
    ],
    team: [
      { to: '/dashboard/team', label: 'My Agents' },
    ],
    agent: [
      { to: '/dashboard/agent', label: 'My Orders' },
    ],
  };

  return (
    <div className="min-h-screen flex">
      <aside className="w-56 bg-gray-900 text-white p-4 flex flex-col">
        <Link to="/" className="text-lg font-bold text-purple-400 mb-6">Zen Fragrances</Link>
        <nav className="flex flex-col gap-1 flex-1">
          {(links[path] || []).map(l => (
            <Link key={l.to} to={l.to}
              className="px-3 py-2 rounded text-sm text-gray-300 hover:bg-gray-800 hover:text-white transition-colors">
              {l.label}
            </Link>
          ))}
        </nav>
        <div className="border-t border-gray-700 pt-3 mt-auto">
          <p className="text-xs text-gray-500 mb-1">{user.name || role}</p>
          <button onClick={logout} className="text-xs text-red-400 hover:text-red-300">Sign Out</button>
        </div>
      </aside>
      <main className="flex-1 bg-gray-50 p-6 overflow-auto">
        <Outlet />
      </main>
    </div>
  );
}
