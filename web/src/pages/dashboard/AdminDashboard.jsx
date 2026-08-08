import { useState, useEffect } from 'react';
import { api } from '../../api';
import FlintChart from '../../components/FlintChart';

export default function AdminDashboard() {
  const [stats, setStats] = useState(null);
  const [daily, setDaily] = useState([]);

  useEffect(() => {
    api('/api/analytics/summary').then(setStats).catch(() => setStats({}));
    api('/api/analytics/daily').then(d => setDaily(d.daily || [])).catch(() => setDaily([]));
  }, []);

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Super Admin Dashboard</h1>
      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
          {[
            { label: 'Total Orders', value: stats.total_orders || '—' },
            { label: 'Revenue', value: `R${stats.revenue || stats.total_revenue || '0'}` },
            { label: 'Active Agents', value: stats.active_agents || '—' },
            { label: 'Team Members', value: stats.team_members || '—' },
          ].map(s => (
            <div key={s.label} className="bg-white rounded-xl p-5 shadow-sm border border-gray-100">
              <p className="text-sm text-gray-500">{s.label}</p>
              <p className="text-2xl font-bold mt-1">{s.value}</p>
            </div>
          ))}
        </div>
      )}
      {daily.length > 0 && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          <FlintChart
            title="Revenue (daily)"
            values={daily}
            semanticTypes={{ day: 'YearMonthDay', revenue: 'Quantity' }}
            chartType="Line Chart"
            xField="day"
            yField="revenue"
          />
          <FlintChart
            title="Orders (daily)"
            values={daily}
            semanticTypes={{ day: 'YearMonthDay', orders: 'Quantity' }}
            chartType="Bar Chart"
            xField="day"
            yField="orders"
          />
        </div>
      )}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <QuickLinks title="Management" links={[
          { to: '/dashboard/admin', label: 'Team Members' },
          { to: '/dashboard/admin', label: 'Products' },
          { to: '/dashboard/admin', label: 'All Orders' },
        ]} />
        <QuickLinks title="Settings" links={[
          { to: '/dashboard/admin', label: 'Message Templates' },
          { to: '/dashboard/admin', label: 'Configure Store' },
        ]} />
      </div>
    </div>
  );
}

function QuickLinks({ title, links }) {
  return (
    <div className="bg-white rounded-xl p-5 shadow-sm border border-gray-100">
      <h3 className="font-semibold mb-3">{title}</h3>
      <div className="flex flex-col gap-2">
        {links.map(l => (
          <span key={l.label} className="text-purple-700 text-sm hover:underline cursor-pointer">{l.label}</span>
        ))}
      </div>
    </div>
  );
}
