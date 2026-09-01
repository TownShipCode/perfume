import { Link } from 'react-router-dom';

export default function RefundPolicy() {
  return (
    <div className="max-w-2xl mx-auto px-4 py-12">
      <Link to="/" className="text-purple-700 text-sm hover:underline">&larr; Back</Link>
      <h1 className="text-3xl font-bold mt-4 mb-4">Returns &amp; Refund Policy</h1>
      <div className="space-y-4 text-sm text-gray-600 leading-relaxed">
        <p>We want you happy with your fragrance. If a product arrives damaged or faulty, tell us within 7 days and we will replace it or refund you.</p>
        <p>Because fragrance is a hygiene product, we cannot accept returns of opened or used bottles unless they are faulty.</p>
        <p>To start a return, send us a message on WhatsApp with your order number and a photo of the issue. We reply within one working day.</p>
        <p>Refunds go back to your original payment method within 5 working days of approval.</p>
      </div>
    </div>
  );
}
