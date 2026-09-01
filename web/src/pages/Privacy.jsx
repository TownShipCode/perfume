import { Link } from 'react-router-dom';

export default function Privacy() {
  return (
    <div className="max-w-2xl mx-auto px-4 py-12">
      <Link to="/" className="text-purple-700 text-sm hover:underline">&larr; Back</Link>
      <h1 className="text-3xl font-bold mt-4 mb-4">Privacy Policy</h1>
      <div className="space-y-4 text-sm text-gray-600 leading-relaxed">
        <p>We collect the minimum needed to run your orders: name, phone number, email, and delivery address.</p>
        <p>We use your details to confirm orders, arrange delivery, and send order updates via WhatsApp and email.</p>
        <p>We never sell your personal information. Payment card details are handled by our payment partners (Yoco), not stored by us.</p>
        <p>You can ask us to delete your data at any time by contacting us.</p>
      </div>
    </div>
  );
}
