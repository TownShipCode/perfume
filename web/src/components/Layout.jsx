import { useState } from 'react';
import { Link, Outlet } from 'react-router-dom';
import { useAuth } from '../useAuth';
import { useCart } from '../useCart';
import { api } from '../api';

export default function Layout() {
  const { user } = useAuth();
  const { count } = useCart();
  const [email, setEmail] = useState('');
  const [subscribed, setSubscribed] = useState(false);

  async function handleSubscribe(e) {
    e.preventDefault();
    if (!email) return;
    try {
      await api('/api/newsletter', { method: 'POST', body: JSON.stringify({ email }) });
      setSubscribed(true);
      setEmail('');
    } catch (err) { /* ignore */ }
  }

  return (
    <div className="min-h-screen flex flex-col">
      {/* Trust banner strip (Fragrance Passion style) */}
      <div className="bg-purple-700 text-white text-xs py-1.5 px-4 flex items-center justify-center gap-4 flex-wrap">
        <span>🚚 Nationwide delivery R65</span>
        <span className="hidden sm:inline">·</span>
        <span>🎁 Free shipping over R2000</span>
        <span className="hidden sm:inline">·</span>
        <Link to="/register/agent" className="font-medium hover:underline">🚀 Become an Agent</Link>
        <span className="hidden sm:inline">·</span>
        <Link to="/scent-finder" className="font-medium hover:underline">✨ Find Your Scent</Link>
      </div>
      <nav className="bg-white border-b border-gray-200 px-6 py-3 flex items-center justify-between sticky top-0 z-50">
        <Link to="/" className="text-xl font-bold text-purple-700 tracking-tight">
          Zen Fragrances
        </Link>
        <div className="flex items-center gap-4 text-sm">
          <Link to="/catalogue" className="text-gray-600 hover:text-purple-700">Catalogue</Link>
          <Link to="/quick-order" className="text-gray-600 hover:text-purple-700 hidden md:inline">Quick Order</Link>
          <Link to="/blog" className="text-gray-600 hover:text-purple-700 hidden md:inline">Blog</Link>
          <Link to="/agents" className="text-gray-600 hover:text-purple-700 hidden md:inline">Find Agent</Link>
          <Link to="/cart" className="relative text-gray-600 hover:text-purple-700">
            🛒
            {count > 0 && <span className="absolute -top-2 -right-2 bg-purple-600 text-white text-[10px] w-4 h-4 rounded-full flex items-center justify-center font-bold">{count}</span>}
          </Link>
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
      <footer className="bg-gray-50 border-t border-gray-200 px-6 py-10 mt-10">
        <div className="max-w-5xl mx-auto grid grid-cols-1 md:grid-cols-3 gap-8 text-sm">
          <div>
            <p className="font-semibold text-gray-700 mb-2">Zen Fragrances</p>
            <p className="text-gray-500">Premium perfume oils for resellers. Buy wholesale, sell at your price.</p>
          </div>
          <div>
            <p className="font-semibold text-gray-700 mb-2">Shop</p>
            <div className="flex flex-col gap-1.5 text-gray-500">
              <Link to="/catalogue" className="hover:text-purple-700">Catalogue</Link>
              <Link to="/quick-order" className="hover:text-purple-700">Quick Order</Link>
              <Link to="/register/agent" className="hover:text-purple-700">Become an Agent</Link>
              <Link to="/agents" className="hover:text-purple-700">Find an Agent</Link>
            </div>
          </div>
          <div>
            <p className="font-semibold text-gray-700 mb-2">Get launch updates</p>
            {subscribed ? (
              <p className="text-green-600 font-medium">✅ Thanks! You're on the list.</p>
            ) : (
              <form onSubmit={handleSubscribe} className="flex gap-2">
                <input type="email" required value={email} onChange={e => setEmail(e.target.value)}
                  placeholder="you@email.com"
                  className="flex-1 min-w-0 border border-gray-300 rounded-lg px-3 py-2 text-sm" />
                <button type="submit" className="bg-purple-700 text-white px-4 py-2 rounded-lg text-sm hover:bg-purple-800">Sign Up</button>
              </form>
            )}
            <div className="flex gap-3 mt-3 text-gray-400 text-xs">
              <Link to="/privacy" className="hover:text-purple-700">Privacy</Link>
              <span>·</span>
              <Link to="/refund-policy" className="hover:text-purple-700">Refunds</Link>
              <span>·</span>
              <Link to="/terms" className="hover:text-purple-700">Terms</Link>
            </div>
          </div>
        </div>
        <p className="text-center text-gray-400 text-xs mt-8">Zen Fragrances &copy; {new Date().getFullYear()} &middot; Nationwide delivery from R65</p>
      </footer>
    </div>
  );
}
