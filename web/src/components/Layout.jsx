import { Link, Outlet } from 'react-router-dom';
import { useAuth } from '../useAuth';

export default function Layout() {
  const { user } = useAuth();
  return (
    <div className="min-h-screen flex flex-col">
      <nav className="bg-white border-b border-gray-200 px-6 py-3 flex items-center justify-between sticky top-0 z-50">
        <Link to="/" className="text-xl font-bold text-purple-700 tracking-tight">
          Zen Fragrances
        </Link>
        <div className="flex items-center gap-4 text-sm">
          <Link to="/catalogue" className="text-gray-600 hover:text-purple-700">Catalogue</Link>
          {user ? (
            <>
              <Link to={`/dashboard/${user.role === 'super_admin' ? 'admin' : user.role === 'manufacturer' ? 'manufacturer' : user.role === 'team_member' ? 'team' : 'agent'}`}
                className="text-gray-600 hover:text-purple-700">Dashboard</Link>
              <span className="text-gray-400">Hi, {user.name || user.role}</span>
            </>
          ) : (
            <>
              <Link to="/login" className="text-purple-700 font-medium">Sign In</Link>
              <Link to="/register" className="bg-purple-700 text-white px-4 py-1.5 rounded-lg text-sm">Register</Link>
            </>
          )}
        </div>
      </nav>
      <main className="flex-1">
        <Outlet />
      </main>
      <footer className="bg-gray-50 border-t border-gray-200 px-6 py-8 text-center text-sm text-gray-500">
        <p>Zen Fragrances &copy; {new Date().getFullYear()} &middot; Premium perfume oils for resellers</p>
        <p className="mt-1">Nationwide delivery from R65 &middot; WhatsApp: {import.meta.env.VITE_WHATSAPP_NUMBER || '012 345 6789'}</p>
      </footer>
    </div>
  );
}
