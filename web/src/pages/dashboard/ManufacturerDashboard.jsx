import { useState, useEffect } from 'react';
import { api } from '../../api';

export default function ManufacturerDashboard() {
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);

  async function load() {
    setLoading(true);
    try { setOrders((await api('/api/orders')).items || []); } catch { setOrders([]); }
    setLoading(false);
  }

  useEffect(() => { load(); }, []);

  async function updateStatus(id, status) {
    try {
      await api(`/api/orders/${id}`, { method: 'PUT', body: JSON.stringify({ status }) });
      load();
    } catch (e) { alert(e.message); }
  }

  if (loading) return <p className="text-gray-500">Loading orders...</p>;

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Manufacturer Dashboard</h1>
      {orders.length === 0 ? (
        <p className="text-gray-500">No orders yet.</p>
      ) : (
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 text-left">
              <tr>
                <th className="px-4 py-3">Order</th>
                <th className="px-4 py-3">Agent</th>
                <th className="px-4 py-3">Total</th>
                <th className="px-4 py-3">Status</th>
                <th className="px-4 py-3">Action</th>
              </tr>
            </thead>
            <tbody>
              {orders.map(o => (
                <tr key={o.id} className="border-t border-gray-100">
                  <td className="px-4 py-3 font-mono text-xs">{o.order_number}</td>
                  <td className="px-4 py-3">{o.agent_code || '—'}</td>
                  <td className="px-4 py-3 font-medium">R{o.total}</td>
                  <td className="px-4 py-3">
                    <span className={`px-2 py-0.5 rounded text-xs font-medium ${
                      o.status === 'pop_waiting' ? 'bg-amber-100 text-amber-800' :
                      o.status === 'confirmed' ? 'bg-blue-100 text-blue-800' :
                      o.status === 'shipped' ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-700'
                    }`}>{o.status}</span>
                  </td>
                  <td className="px-4 py-3">
                    {o.status === 'pop_waiting' && (
                      <button onClick={() => updateStatus(o.id, 'confirmed')}
                        className="bg-purple-700 text-white px-3 py-1 rounded text-xs hover:bg-purple-800">
                        Confirm
                      </button>
                    )}
                    {o.status === 'confirmed' && (
                      <button onClick={() => updateStatus(o.id, 'shipped')}
                        className="bg-green-600 text-white px-3 py-1 rounded text-xs hover:bg-green-700">
                        Ship
                      </button>
                    )}
                    {o.status === 'shipped' && <span className="text-green-600 text-xs">✅</span>}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
