import { useState } from 'react';
import { Link } from 'react-router-dom';
import { api } from '../api';

export default function ForgotPassword() {
  const [email, setEmail] = useState('');
  const [sent, setSent] = useState(false);
  const [error, setError] = useState('');

  async function handleSubmit(e) {
    e.preventDefault();
    setError('');
    try {
      await api('/api/auth/forgot-password', { method: 'POST', body: JSON.stringify({ email }) });
      setSent(true);
    } catch (err) {
      setError(err.message);
    }
  }

  if (sent) return (
    <div className="max-w-sm mx-auto px-4 py-16 text-center">
      <p className="text-green-600 text-lg font-medium">If that email exists, a reset link has been sent.</p>
      <Link to="/login" className="text-purple-700 mt-4 inline-block">Back to Sign In</Link>
    </div>
  );

  return (
    <div className="max-w-sm mx-auto px-4 py-12">
      <h1 className="text-2xl font-bold text-center mb-6">Forgot Password</h1>
      <form onSubmit={handleSubmit} className="flex flex-col gap-3">
        {error && <p className="text-red-600 text-sm">{error}</p>}
        <input type="email" placeholder="Email" value={email} onChange={e => setEmail(e.target.value)}
          className="border border-gray-300 rounded-lg px-4 py-2 text-sm" required />
        <button type="submit"
          className="bg-purple-700 text-white py-2.5 rounded-lg font-medium hover:bg-purple-800 transition-colors">
          Send Reset Link
        </button>
      </form>
      <p className="text-center text-sm text-gray-500 mt-4">
        <Link to="/login" className="text-purple-700">Back to Sign In</Link>
      </p>
    </div>
  );
}
