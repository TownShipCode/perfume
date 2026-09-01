import { useState, useEffect } from 'react';
import { api } from '../api';

export default function AgentLocator() {
  const [suburb, setSuburb] = useState('');
  const [agents, setAgents] = useState([]);
  const [searched, setSearched] = useState(false);
  const [loading, setLoading] = useState(false);

  const search = async () => {
    if (!suburb.trim()) return;
    setLoading(true);
    setSearched(true);
    try {
      const d = await api(`/api/agents/search?suburb=${encodeURIComponent(suburb.trim())}`);
      setAgents(d.agents || []);
    } catch { setAgents([]); }
    setLoading(false);
  };

  return (
    <div className="max-w-3xl mx-auto px-4 py-8">
      <h1 className="text-2xl font-bold mb-2">Find an Agent</h1>
      <p className="text-gray-500 mb-6 text-sm">Find a Zen Fragrances agent near you to browse and buy in person.</p>

      <div className="flex gap-2 mb-6">
        <input type="text" placeholder="Enter your suburb or area..." value={suburb}
          onChange={e => setSuburb(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && search()}
          className="flex-1 border border-gray-300 rounded-lg px-4 py-3 text-sm" />
        <button onClick={search} disabled={loading}
          className="bg-purple-600 text-white px-6 py-3 rounded-lg font-medium hover:bg-purple-700 disabled:opacity-50 transition-colors">
          {loading ? 'Searching...' : 'Search'}
        </button>
      </div>

      {searched && (
        agents.length === 0 ? (
          <div className="bg-purple-50 border border-purple-200 rounded-xl p-6 text-center">
            <p className="text-purple-800 font-medium">No agents found in "{suburb}"</p>
            <p className="text-sm text-purple-600 mt-1">Try a nearby suburb or browse our online catalogue.</p>
          </div>
        ) : (
          <div className="space-y-3">
            <p className="text-sm text-gray-500">{agents.length} agent{agents.length !== 1 ? 's' : ''} found near "{suburb}"</p>
            {agents.map(a => (
              <div key={a.agent_code} className="bg-white rounded-xl border border-gray-100 shadow-sm p-4 flex items-center justify-between gap-3">
                <div>
                  <h3 className="font-semibold">{a.name || 'Agent'}</h3>
                  <p className="text-sm text-gray-500">{a.suburb}{a.city ? `, ${a.city}` : ''}</p>
                  {a.bio && <p className="text-xs text-gray-400 mt-1">{a.bio}</p>}
                </div>
                <a href={`https://wa.me/${a.phone_number}`} target="_blank" rel="noopener noreferrer"
                  className="bg-green-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-green-700 transition-colors whitespace-nowrap">
                  WhatsApp
                </a>
              </div>
            ))}
          </div>
        )
      )}
    </div>
  );
}
