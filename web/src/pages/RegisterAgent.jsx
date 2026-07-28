import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { registerAgent } from '../api';

export default function RegisterAgent() {
  const [form, setForm] = useState({ name: '', surname: '', phone: '', team_code: '', email: '', password: '' });
  const [error, setError] = useState('');
  const [result, setResult] = useState(null);
  const nav = useNavigate();

  function set(k) { return e => setForm(f => ({ ...f, [k]: e.target.value })); }

  async function handleSubmit(e) {
    e.preventDefault();
    setError('');
    try {
      const data = await registerAgent(form);
      setResult(data);
    } catch (err) {
      setError(err.message);
    }
  }

  if (result) return (
    <div className="max-w-sm mx-auto px-4 py-16 text-center">
      <p className="text-green-600 text-xl font-bold mb-2">✅ Welcome, Agent!</p>
      <p className="text-gray-700">Your agent code: <strong>{result.agent_code}</strong></p>
      <p className="text-red-600 font-bold mt-2">🔐 Recovery PIN: {result.recovery_pin} — save this!</p>
      <p className="text-sm text-gray-500 mt-4">You can now order via WhatsApp or sign in to your dashboard.</p>
      <Link to="/login" className="inline-block mt-4 bg-purple-700 text-white px-6 py-2 rounded-lg">Sign In</Link>
    </div>
  );

  return (
    <div className="max-w-sm mx-auto px-4 py-12">
      <h1 className="text-2xl font-bold text-center mb-2">Become an Agent</h1>
      <p className="text-center text-sm text-gray-500 mb-6">Enter your team member&apos;s code to register.</p>
      <form onSubmit={handleSubmit} className="flex flex-col gap-3">
        {error && <p className="text-red-600 text-sm">{error}</p>}
        <input placeholder="First Name" value={form.name} onChange={set('name')}
          className="border border-gray-300 rounded-lg px-4 py-2 text-sm" required />
        <input placeholder="Surname" value={form.surname} onChange={set('surname')}
          className="border border-gray-300 rounded-lg px-4 py-2 text-sm" required />
        <input type="tel" placeholder="Phone (e.g. 0821234567)" value={form.phone} onChange={set('phone')}
          className="border border-gray-300 rounded-lg px-4 py-2 text-sm" required />
        <input placeholder="Team Code (from your team member)" value={form.team_code} onChange={set('team_code')}
          className="border border-gray-300 rounded-lg px-4 py-2 text-sm font-mono uppercase" required />
        <input type="email" placeholder="Email (optional)" value={form.email} onChange={set('email')}
          className="border border-gray-300 rounded-lg px-4 py-2 text-sm" />
        <input type="password" placeholder="Password (optional)" value={form.password} onChange={set('password')}
          className="border border-gray-300 rounded-lg px-4 py-2 text-sm" />
        <button type="submit"
          className="bg-purple-700 text-white py-2.5 rounded-lg font-medium hover:bg-purple-800 transition-colors">
          Register as Agent
        </button>
      </form>
      <p className="text-center text-sm text-gray-500 mt-4">
        Already registered? <Link to="/login" className="text-purple-700">Sign In</Link>
      </p>
    </div>
  );
}
