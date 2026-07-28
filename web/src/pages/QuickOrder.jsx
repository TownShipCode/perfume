import { useState, useEffect, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { api } from '../api';

export default function QuickOrder() {
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [quantities, setQuantities] = useState({});
  const [search, setSearch] = useState('');

  useEffect(() => {
    api('/api/products?page_size=100').then(d => {
      setProducts(d.items || d.products || []);
      setLoading(false);
    }).catch(() => setLoading(false));
  }, []);

  const setQty = useCallback((productId, value) => {
    setQuantities(prev => {
      const next = { ...prev };
      const n = parseInt(value) || 0;
      if (n <= 0) { delete next[productId]; }
      else { next[productId] = Math.min(n, 99); }
      return next;
    });
  }, []);

  const selected = Object.entries(quantities).filter(([, q]) => q > 0);
  const cartItems = selected.map(([pid, qty]) => {
    const p = products.find(x => x.id === parseInt(pid));
    return p ? { ...p, qty } : null;
  }).filter(Boolean);

  const total = cartItems.reduce((sum, p) => sum + parseFloat(p.price) * p.qty, 0);

  const buildWhatsappMsg = () => {
    const lines = cartItems.map(p => `${p.qty}x ${p.name}`);
    return encodeURIComponent(lines.join('\n'));
  };
  const WA_NUMBER = import.meta.env.VITE_WHATSAPP_NUMBER || '27123456789';
  const waLink = `https://wa.me/${WA_NUMBER}?text=${buildWhatsappMsg()}`;

  const filtered = search ? products.filter(p => p.name.toLowerCase().includes(search.toLowerCase())) : products;

  if (loading) return <div className="max-w-6xl mx-auto px-4 py-12 text-center text-gray-500">Loading products...</div>;

  return (
    <div className="max-w-6xl mx-auto px-4 py-8">
      <div className="flex flex-wrap items-center justify-between gap-4 mb-6">
        <div>
          <h1 className="text-2xl font-bold">⚡ Quick Order</h1>
          <p className="text-sm text-gray-500 mt-1">Add quantities and send your order via WhatsApp</p>
        </div>
        <Link to="/catalogue" className="text-purple-700 text-sm hover:underline">&larr; Browse with filters</Link>
      </div>

      {/* Search */}
      <input type="text" placeholder="Filter products..." value={search} onChange={e => setSearch(e.target.value)}
        className="w-full border border-gray-300 rounded-lg px-4 py-2 text-sm mb-4" />

      {/* Product Grid */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-3 mb-8">
        {filtered.map(p => {
          const qty = quantities[p.id] || 0;
          const isSelected = qty > 0;
          return (
            <div key={p.id}
              className={`bg-white rounded-xl border overflow-hidden transition-all ${isSelected ? 'border-purple-400 shadow-md ring-1 ring-purple-200' : 'border-gray-100 shadow-sm'}`}>
              <div className="aspect-square bg-gray-50 flex items-center justify-center text-3xl relative">
                {p.image_url ? <img src={p.image_url} alt={p.name} className="w-full h-full object-cover" /> : '🫧'}
                {isSelected && <span className="absolute top-1 right-1 bg-purple-600 text-white text-xs w-5 h-5 rounded-full flex items-center justify-center font-bold">{qty}</span>}
              </div>
              <div className="p-2">
                <h3 className="font-medium text-xs truncate">{p.name}</h3>
                <p className="text-purple-700 font-bold text-sm">R{p.price}</p>
                <div className="flex items-center gap-1 mt-1">
                  <button onClick={() => setQty(p.id, qty - 1)} disabled={qty === 0}
                    className="w-7 h-7 rounded bg-gray-100 text-gray-600 text-sm font-bold disabled:opacity-30 hover:bg-gray-200">−</button>
                  <input type="number" min="0" max="99" value={qty || ''} placeholder="0"
                    onChange={e => setQty(p.id, e.target.value)}
                    className="w-10 text-center text-sm border border-gray-200 rounded py-0.5" />
                  <button onClick={() => setQty(p.id, qty + 1)}
                    className="w-7 h-7 rounded bg-purple-100 text-purple-700 text-sm font-bold hover:bg-purple-200">+</button>
                </div>
                {p.stock_quantity != null && p.stock_quantity <= 5 && (
                  <p className="text-amber-600 text-[10px] mt-0.5">⚠️ {p.stock_quantity} left</p>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {/* Order Summary Bar — fixed at bottom when items selected */}
      {selected.length > 0 && (
        <div className="fixed bottom-0 left-0 right-0 bg-white border-t border-gray-200 shadow-lg p-4 z-40">
          <div className="max-w-6xl mx-auto flex flex-wrap items-center justify-between gap-3">
            <div className="text-sm">
              <span className="font-semibold">{selected.length} products</span>
              <span className="text-gray-500 ml-2">{cartItems.map(p => `${p.qty}× ${p.name}`).join(', ').slice(0, 80)}{cartItems.length > 2 ? '...' : ''}</span>
            </div>
            <div className="flex items-center gap-3">
              <span className="font-bold text-purple-700">R{total.toFixed(2)}</span>
              <a href={waLink} target="_blank" rel="noopener noreferrer"
                className="bg-green-600 text-white px-5 py-2 rounded-lg font-medium text-sm hover:bg-green-700 transition-colors">
                📱 Send via WhatsApp
              </a>
              <button onClick={() => setQuantities({})}
                className="text-gray-500 hover:text-red-600 text-sm">Clear</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
