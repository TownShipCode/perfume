import { useState, useEffect } from 'react';
import { api } from '../../api';
import { useAuth } from '../../useAuth';

export default function AgentDashboard() {
  const { user } = useAuth();
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const code = user?.agent_code;
    if (code) {
      api(`/api/orders?agent_code=${code}`).then(d => setOrders(d.items || [])).catch(() => setOrders([])).finally(() => setLoading(false));
    } else {
      setLoading(false);
    }
  }, [user]);

  if (loading) return <p className="text-gray-500">Loading...</p>;

  const total = orders.reduce((sum, o) => sum + (parseFloat(o.total) || 0), 0);

  return (
    <div>
      <h1 className="text-2xl font-bold mb-2">Agent Dashboard</h1>
      <p className="text-gray-500 mb-6">Agent Code: <span className="font-mono font-bold">{user?.agent_code || '—'}</span></p>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
        <div className="bg-white rounded-xl p-5 shadow-sm border border-gray-100">
          <p className="text-sm text-gray-500">Total Orders</p>
          <p className="text-2xl font-bold mt-1">{orders.length}</p>
        </div>
        <div className="bg-white rounded-xl p-5 shadow-sm border border-gray-100">
          <p className="text-sm text-gray-500">Total Sales</p>
          <p className="text-2xl font-bold mt-1">R{total.toFixed(2)}</p>
        </div>
        <div className="bg-white rounded-xl p-5 shadow-sm border border-gray-100">
          <p className="text-sm text-gray-500">Pending</p>
          <p className="text-2xl font-bold mt-1">{orders.filter(o => o.status === 'pop_waiting' || o.status === 'pending').length}</p>
        </div>
      </div>

      <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
        <h3 className="font-semibold p-5 pb-0">My Orders</h3>
        {orders.length === 0 ? (
          <p className="p-5 text-gray-500 text-sm">No orders yet. Order via WhatsApp to get started!</p>
        ) : (
          <table className="w-full text-sm">
            <thead className="bg-gray-50 text-left">
              <tr><th className="px-4 py-3">Order</th><th className="px-4 py-3">Total</th><th className="px-4 py-3">Status</th></tr>
            </thead>
            <tbody>
              {orders.map(o => (
                <tr key={o.id} className="border-t border-gray-100">
                  <td className="px-4 py-3 font-mono text-xs">{o.order_number}</td>
                  <td className="px-4 py-3 font-medium">R{o.total}</td>
                  <td className="px-4 py-3">
                    <span className={`px-2 py-0.5 rounded text-xs font-medium ${
                      o.status === 'shipped' ? 'bg-green-100 text-green-800' :
                      o.status === 'confirmed' ? 'bg-blue-100 text-blue-800' :
                      o.status === 'pop_waiting' ? 'bg-purple-100 text-purple-800' :
                      'bg-gray-100 text-gray-700'
                    }`}>{o.status}</span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
