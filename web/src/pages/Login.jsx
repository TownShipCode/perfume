import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { login } from '../api';
import { useAuth } from '../useAuth';

const ROLE_REDIRECT = { super_admin: '/dashboard/admin', manufacturer: '/dashboard/manufacturer', team_member: '/dashboard/team', agent: '/dashboard/agent' };

export default function Login() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { setUser } = useAuth();
  const nav = useNavigate();

  async function handleSubmit(e) {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      const data = await login(email, password);
      setUser({ role: data.role, name: data.name, agent_code: data.agent_code });
      nav(ROLE_REDIRECT[data.role] || '/');
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="max-w-sm mx-auto px-4 py-16">
      <h1 className="text-2xl font-bold text-center mb-6">Sign In</h1>
      <form onSubmit={handleSubmit} className="flex flex-col gap-4">
        {error && <p className="text-red-600 text-sm">{error}</p>}
        <input type="email" placeholder="Email" value={email} onChange={e => setEmail(e.target.value)}
          className="border border-gray-300 rounded-lg px-4 py-2 text-sm" required />
        <input type="password" placeholder="Password" value={password} onChange={e => setPassword(e.target.value)}
          className="border border-gray-300 rounded-lg px-4 py-2 text-sm" required />
        <button type="submit" disabled={loading}
          className="bg-purple-700 text-white py-2.5 rounded-lg font-medium hover:bg-purple-800 transition-colors disabled:opacity-50">
          {loading ? 'Signing in...' : 'Sign In'}
        </button>
      </form>
      <p className="text-center text-sm text-gray-500 mt-4">
        Don&apos;t have an account? <Link to="/register" className="text-purple-700">Register</Link>
      </p>
    </div>
  );
}
