import { Link } from 'react-router-dom';

export default function OrderConfirmed() {
  return (
    <div className="max-w-lg mx-auto px-4 py-16 text-center">
      <p className="text-5xl mb-4 font-serif font-bold text-green-600">✓</p>
      <h1 className="text-2xl font-bold mb-2">Order Confirmed!</h1>
      <p className="text-gray-500 mb-6">
        Your order has been placed. We'll process it and notify you once it's on the way.
      </p>
      <p className="text-sm text-gray-400 mb-8">
        For EFT payments, please send your proof of payment via WhatsApp to complete your order.
      </p>
      <div className="flex gap-3 justify-center">
        <Link to="/catalogue" className="bg-purple-700 text-white px-6 py-3 rounded-xl font-medium hover:bg-purple-800 transition-colors">
          Continue Shopping
        </Link>
        <Link to="/" className="border border-gray-300 text-gray-700 px-6 py-3 rounded-xl font-medium hover:bg-gray-50 transition-colors">
          Home
        </Link>
      </div>
    </div>
  );
}
