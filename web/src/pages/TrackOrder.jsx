import { useState } from 'react';
import { api } from '../api';

const STATUS_LABELS = {
  pending: { label: 'Pending', css: 'bg-gray-100 text-gray-800' },
  pop_waiting: { label: 'Waiting for POP', css: 'bg-gray-100 text-gray-800' },
  confirmed: { label: 'Confirmed', css: 'bg-blue-100 text-blue-800' },
  shipped: { label: 'Shipped', css: 'bg-green-100 text-green-800' },
  cancelled: { label: 'Cancelled', css: 'bg-red-100 text-red-800' },
};

export default function TrackOrder() {
  const [phone, setPhone] = useState('');
  const [orders, setOrders] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  async function handleSubmit(e) {
    e.preventDefault();
    if (!phone.trim()) return;
    setLoading(true);
    setError('');
    try {
      const d = await api(`/api/orders/track?phone=${encodeURIComponent(phone.trim())}`);
      setOrders(d.items || []);
    } catch (err) {
      setError(err.message || 'Failed to load orders.');
      setOrders(null);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="max-w-3xl mx-auto px-4 py-8">
      <h1 className="text-2xl font-bold mb-2">Track My Order</h1>
      <p className="text-gray-500 mb-6 text-sm">Enter the phone number you ordered with to see your latest orders and delivery status.</p>

      <form onSubmit={handleSubmit} className="flex gap-2 mb-6">
        <input type="tel" required value={phone} onChange={e => setPhone(e.target.value)}
          placeholder="e.g. 0821234567"
          className="flex-1 border border-gray-300 rounded-lg px-4 py-3 text-sm" />
        <button type="submit" disabled={loading}
          className="bg-purple-600 text-white px-6 py-3 rounded-lg font-medium hover:bg-purple-700 disabled:opacity-50 transition-colors">
          {loading ? 'Checking...' : 'Track'}
        </button>
      </form>

      {error && <p className="text-red-600 text-sm mb-4">{error}</p>}

      {orders !== null && orders.length === 0 && (
        <p className="text-gray-500 text-center py-8">No orders found for that number.</p>
      )}

      {orders !== null && orders.length > 0 && (
        <div className="space-y-4">
          {orders.map(o => {
            const st = STATUS_LABELS[o.status] || { label: o.status, css: 'bg-gray-100 text-gray-700' };
            return (
              <div key={o.id} className="bg-white rounded-xl border border-gray-100 shadow-sm p-5">
                <div className="flex items-center justify-between mb-2">
                  <p className="font-semibold text-gray-800">Order #{o.order_number}</p>
                  <span className={`text-xs font-medium px-2.5 py-1 rounded-full ${st.css}`}>{st.label}</span>
                </div>
                <p className="text-sm text-gray-500">Total: <span className="font-medium text-gray-700">R{o.total}</span></p>
                {o.tracking_info && <p className="text-sm text-gray-500 mt-1">Waybill: {o.tracking_info}</p>}
                <p className="text-xs text-gray-400 mt-2">{new Date(o.created_at).toLocaleString()}</p>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
