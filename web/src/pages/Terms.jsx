import { Link } from 'react-router-dom';

export default function Terms() {
  return (
    <div className="max-w-2xl mx-auto px-4 py-12">
      <Link to="/" className="text-purple-700 text-sm hover:underline">&larr; Back</Link>
      <h1 className="text-3xl font-bold mt-4 mb-4">Terms of Service</h1>
      <div className="space-y-4 text-sm text-gray-600 leading-relaxed">
        <p>Zen Fragrances sells wholesale perfume oils inspired by designer scents. They are interpretations, not original designer products.</p>
        <p>Prices shown are wholesale. Agents set their own retail prices.</p>
        <p>Orders placed via the website or WhatsApp are confirmed once payment is received.</p>
        <p>We deliver nationwide via The Courier Guy. Delivery times are estimates, not guarantees.</p>
        <p>If you become an agent, your agent code and recovery PIN are your responsibility. Keep them safe.</p>
      </div>
    </div>
  );
}
