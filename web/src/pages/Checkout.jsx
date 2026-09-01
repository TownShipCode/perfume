import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useCart } from '../useCart';
import { api } from '../api';
import { useConfig, shippingFee, freeThreshold } from '../useConfig';

export default function Checkout() {
  const { items, total, clearCart } = useCart();
  const navigate = useNavigate();
  const config = useConfig();
  const shipFee = shippingFee(config);
  const threshold = freeThreshold(config);
  const [form, setForm] = useState({ name: '', surname: '', email: '', phone: '', area: '', street: '', city: '', postal_code: '', province: '' });
  const [payment, setPayment] = useState('yoco');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');

  const shipping = total >= threshold ? 0 : shipFee;

  if (items.length === 0) return (
    <div className="max-w-lg mx-auto px-4 py-16 text-center">
      <p className="text-gray-500">Your cart is empty. <Link to="/catalogue" className="text-purple-700 hover:underline">Browse catalogue</Link></p>
    </div>
  );

  const set = (field) => (e) => setForm(prev => ({ ...prev, [field]: e.target.value }));

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!form.name || !form.phone || !form.street || !form.city) {
      setError('Please fill in name, phone, street, and city at minimum.');
      return;
    }
    setSubmitting(true);
    setError('');
    try {
      const payload = {
        items: items.map(i => ({ product_id: i.id, quantity: i.qty })),
        ...form,
        payment_method: payment,
      };
      const result = await api('/api/orders/web', { method: 'POST', body: JSON.stringify(payload) });
      clearCart();
      const orderId = result.order?.id;
      if (result.checkout_url) {
        window.location.href = result.checkout_url;
      } else {
        navigate(`/order/${orderId}/confirmed`);
      }
    } catch (err) {
      setError(err.message || 'Failed to place order. Please try again.');
      setSubmitting(false);
    }
  };

  const input = (field, label, type = 'text', required = false) => (
    <div>
      <label className="block text-sm font-medium text-gray-700 mb-1">{label}{required && ' *'}</label>
      <input type={type} value={form[field]} onChange={set(field)} required={required}
        className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm" />
    </div>
  );

  return (
    <div className="max-w-lg mx-auto px-4 py-8">
      <h1 className="text-2xl font-bold mb-6">Checkout</h1>

      <div className="bg-white rounded-xl border border-gray-100 shadow-sm p-4 mb-4 text-sm">
        <p className="font-semibold mb-2">Order Summary</p>
        {items.map(i => <p key={i.id} className="text-gray-600">{i.qty}× {i.name} — R{(parseFloat(i.price) * i.qty).toFixed(2)}</p>)}
        <p className="text-xs text-gray-400 mt-1">Delivery: {shipping === 0 ? 'FREE' : `R${shipping}.00`}</p>
        <p className="font-bold text-purple-700 mt-2">Total: R{(total + shipping).toFixed(2)}</p>
      </div>

      {error && <p className="bg-red-50 text-red-700 text-sm rounded-lg p-3 mb-4">{error}</p>}

      <form onSubmit={handleSubmit} className="space-y-4">
        <p className="font-semibold text-sm text-gray-700">Delivery Details</p>
        <div className="grid grid-cols-2 gap-3">
          {input('name', 'First Name', 'text', true)}
          {input('surname', 'Surname')}
        </div>
        {input('email', 'Email')}
        {input('phone', 'Phone', 'tel', true)}
        {input('street', 'Street & House Number', 'text', true)}
        {input('area', 'Area / Suburb')}
        <div className="grid grid-cols-2 gap-3">
          {input('city', 'City', 'text', true)}
          {input('postal_code', 'Postal Code')}
        </div>
        {input('province', 'Province')}

        <div className="pt-2">
          <p className="font-semibold text-sm text-gray-700 mb-2">Payment Method</p>
          <div className="flex gap-3">
            <label className={`flex-1 border rounded-lg p-3 cursor-pointer text-center text-sm ${payment === 'yoco' ? 'border-purple-500 bg-purple-50' : 'border-gray-200'}`}>
              <input type="radio" name="payment" value="yoco" checked={payment === 'yoco'} onChange={() => setPayment('yoco')} className="sr-only" />
              <span className="text-lg">💳</span>
              <p className="font-medium">Yoco</p>
              <p className="text-xs text-gray-500">Card / Instant EFT</p>
            </label>
            <label className={`flex-1 border rounded-lg p-3 cursor-pointer text-center text-sm ${payment === 'eft' ? 'border-purple-500 bg-purple-50' : 'border-gray-200'}`}>
              <input type="radio" name="payment" value="eft" checked={payment === 'eft'} onChange={() => setPayment('eft')} className="sr-only" />
              <span className="text-lg">🏦</span>
              <p className="font-medium">EFT</p>
              <p className="text-xs text-gray-500">Manual deposit</p>
            </label>
          </div>
        </div>

        <button type="submit" disabled={submitting}
          className="w-full bg-purple-700 text-white py-3 rounded-xl font-medium text-lg hover:bg-purple-800 disabled:opacity-50 transition-colors">
          {submitting ? 'Placing order...' : `Place Order — R${(total + shipping).toFixed(2)}`}
        </button>
      </form>
    </div>
  );
}
