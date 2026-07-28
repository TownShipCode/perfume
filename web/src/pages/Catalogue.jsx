import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { api } from '../api';

export default function Catalogue() {
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [category, setCategory] = useState('');
  const [categories, setCategories] = useState([]);

  useEffect(() => {
    api('/api/products/categories').then(d => setCategories(d.items || [])).catch(() => {});
  }, []);

  useEffect(() => {
    setLoading(true);
    const params = new URLSearchParams();
    if (search) params.set('search', search);
    if (category) params.set('category', category);
    params.set('page_size', '24');
    api(`/api/products?${params}`)
      .then(d => setProducts(d.items || d.products || []))
      .catch(() => setProducts([]))
      .finally(() => setLoading(false));
  }, [search, category]);

  return (
    <div className="max-w-6xl mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold mb-6">Catalogue</h1>

      <div className="flex gap-4 mb-6 flex-wrap">
        <input
          type="text" placeholder="Search fragrances..."
          value={search} onChange={e => setSearch(e.target.value)}
          className="flex-1 min-w-[200px] border border-gray-300 rounded-lg px-4 py-2 text-sm"
        />
        <select value={category} onChange={e => setCategory(e.target.value)}
          className="border border-gray-300 rounded-lg px-4 py-2 text-sm bg-white">
          <option value="">All Categories</option>
          {categories.map(c => <option key={c.name} value={c.name}>{c.name}</option>)}
        </select>
      </div>

      {loading ? (
        <p className="text-gray-500 text-center py-12">Loading...</p>
      ) : products.length === 0 ? (
        <p className="text-gray-500 text-center py-12">No products found.</p>
      ) : (
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
          {products.map(p => (
            <Link key={p.id} to={`/product/${p.id}`}
              className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden hover:shadow-md transition-shadow">
              <div className="aspect-square bg-gray-100 flex items-center justify-center text-4xl">
                {p.image_url ? <img src={p.image_url} alt={p.name} className="w-full h-full object-cover" /> : '🫧'}
              </div>
              <div className="p-3">
                <h3 className="font-medium text-sm truncate">{p.name}</h3>
                <p className="text-purple-700 font-bold mt-1">R{p.price}</p>
                {p.stock_quantity != null && (
                  <p className={`text-xs mt-1 ${p.stock_quantity > 5 ? 'text-green-600' : p.stock_quantity > 0 ? 'text-amber-600' : 'text-red-600'}`}>
                    {p.stock_quantity > 0 ? `${p.stock_quantity} in stock` : 'Out of stock'}
                  </p>
                )}
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
