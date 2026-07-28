import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { register } from '../api';

export default function Register() {
  const [form, setForm] = useState({ name: '', surname: '', email: '', phone: '', password: '' });
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);
  const nav = useNavigate();

  function set(k) { return e => setForm(f => ({ ...f, [k]: e.target.value })); }

  async function handleSubmit(e) {
    e.preventDefault();
    setError('');
    try {
      await register(form);
      setSuccess(true);
      setTimeout(() => nav('/login'), 2000);
    } catch (err) {
      setError(err.message);
    }
  }

  if (success) return (
    <div className="max-w-sm mx-auto px-4 py-16 text-center">
      <p className="text-green-600 text-lg font-medium">✅ Registered! Redirecting to sign in...</p>
    </div>
  );

  return (
    <div className="max-w-sm mx-auto px-4 py-12">
      <h1 className="text-2xl font-bold text-center mb-6">Create Account</h1>
      <form onSubmit={handleSubmit} className="flex flex-col gap-3">
        {error && <p className="text-red-600 text-sm">{error}</p>}
        <input placeholder="First Name" value={form.name} onChange={set('name')}
          className="border border-gray-300 rounded-lg px-4 py-2 text-sm" required />
        <input placeholder="Surname" value={form.surname} onChange={set('surname')}
          className="border border-gray-300 rounded-lg px-4 py-2 text-sm" required />
        <input type="email" placeholder="Email" value={form.email} onChange={set('email')}
          className="border border-gray-300 rounded-lg px-4 py-2 text-sm" required />
        <input type="tel" placeholder="Phone (e.g. 0821234567)" value={form.phone} onChange={set('phone')}
          className="border border-gray-300 rounded-lg px-4 py-2 text-sm" required />
        <input type="password" placeholder="Password" value={form.password} onChange={set('password')}
          className="border border-gray-300 rounded-lg px-4 py-2 text-sm" required />
        <button type="submit"
          className="bg-purple-700 text-white py-2.5 rounded-lg font-medium hover:bg-purple-800 transition-colors">
          Register
        </button>
      </form>
      <p className="text-center text-sm text-gray-500 mt-4">
        Already have an account? <Link to="/login" className="text-purple-700">Sign In</Link>
      </p>
      <p className="text-center text-sm text-gray-500 mt-2">
        Want to become an agent? <Link to="/register/agent" className="text-purple-700">Register as Agent</Link>
      </p>
    </div>
  );
}
