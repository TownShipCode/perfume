import { useState, useEffect } from 'react';
import { api } from '../../api';

export default function TeamDashboard() {
  const [agents, setAgents] = useState([]);
  const [orders, setOrders] = useState([]);
  const [commission, setCommission] = useState(0);

  useEffect(() => {
    api('/api/orders?team_member_id=me').then(d => setOrders(d.items || [])).catch(() => {});
    api('/api/customers?role=agent').then(d => setAgents(d.items || [])).catch(() => {});
  }, []);

  useEffect(() => {
    const total = orders.reduce((sum, o) => sum + (parseFloat(o.commission_amount) || 0), 0);
    setCommission(total);
  }, [orders]);

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Team Member Dashboard</h1>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
        <StatCard label="My Agents" value={agents.length} />
        <StatCard label="Agent Orders" value={orders.length} />
        <StatCard label="Commission" value={`R${commission.toFixed(2)}`} />
      </div>
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-5">
        <h3 className="font-semibold mb-3">My Agents</h3>
        {agents.length === 0 ? <p className="text-gray-500 text-sm">No agents yet.</p> : (
          <table className="w-full text-sm">
            <thead className="text-left"><tr><th className="py-2">Name</th><th className="py-2">Agent Code</th><th className="py-2">Phone</th></tr></thead>
            <tbody>
              {agents.map(a => (
                <tr key={a.id} className="border-t border-gray-100">
                  <td className="py-2">{a.name} {a.surname}</td>
                  <td className="py-2 font-mono">{a.agent_code}</td>
                  <td className="py-2">{a.phone_number}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}

function StatCard({ label, value }) {
  return (
    <div className="bg-white rounded-xl p-5 shadow-sm border border-gray-100">
      <p className="text-sm text-gray-500">{label}</p>
      <p className="text-2xl font-bold mt-1">{value}</p>
    </div>
  );
}
