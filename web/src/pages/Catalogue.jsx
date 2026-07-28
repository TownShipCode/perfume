import { useState, useEffect, useRef } from 'react';
import { Link } from 'react-router-dom';
import { api } from '../api';

const GENDER_ICONS = { men: '👨', women: '👩', unisex: '👥' };

export default function Catalogue() {
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [category, setCategory] = useState('');
  const [gender, setGender] = useState('');
  const [scentFamily, setScentFamily] = useState('');
  const [categories, setCategories] = useState([]);
  const [scents, setScents] = useState([]);
  const [genders, setGenders] = useState([]);

  const [debouncedSearch, setDebouncedSearch] = useState('');
  const timerRef = useRef(null);

  useEffect(() => {
    api('/api/products/categories').then(d => setCategories(d.items || [])).catch(() => {});
    api('/api/products/scents').then(d => {
      setScents(d.scent_families || []);
      setGenders(d.genders || []);
    }).catch(() => {});
  }, []);

  useEffect(() => {
    if (timerRef.current) clearTimeout(timerRef.current);
    timerRef.current = setTimeout(() => setDebouncedSearch(search), 300);
    return () => clearTimeout(timerRef.current);
  }, [search]);

  useEffect(() => {
    setLoading(true);
    const params = new URLSearchParams();
    if (debouncedSearch) params.set('search', debouncedSearch);
    if (category) params.set('category', category);
    if (gender) params.set('gender', gender);
    if (scentFamily) params.set('scent_family', scentFamily);
    params.set('page_size', '24');
    api(`/api/products?${params}`)
      .then(d => setProducts(d.items || d.products || []))
      .catch(() => setProducts([]))
      .finally(() => setLoading(false));
  }, [debouncedSearch, category, gender, scentFamily]);

  const clearAll = () => { setCategory(''); setGender(''); setScentFamily(''); setSearch(''); };

  return (
    <div className="max-w-6xl mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold mb-6">Catalogue</h1>

      {/* Search + Category */}
      <div className="flex gap-4 mb-4 flex-wrap">
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

      {/* Filter chips — Gender */}
      {genders.length > 0 && (
        <div className="flex gap-2 mb-2 flex-wrap">
          <span className="text-xs text-gray-500 self-center mr-1">Gender:</span>
          {genders.map(g => (
            <button key={g} onClick={() => setGender(gender === g ? '' : g)}
              className={`px-3 py-1 rounded-full text-xs font-medium border transition-colors ${
                gender === g ? 'bg-purple-600 text-white border-purple-600' : 'bg-white text-gray-700 border-gray-300 hover:border-purple-400'
              }`}>
              {GENDER_ICONS[g] || ''} {g}
            </button>
          ))}
        </div>
      )}

      {/* Filter chips — Scent Family */}
      {scents.length > 0 && (
        <div className="flex gap-2 mb-4 flex-wrap">
          <span className="text-xs text-gray-500 self-center mr-1">Scent:</span>
          {scents.map(s => (
            <button key={s} onClick={() => setScentFamily(scentFamily === s ? '' : s)}
              className={`px-3 py-1 rounded-full text-xs font-medium border transition-colors ${
                scentFamily === s ? 'bg-amber-600 text-white border-amber-600' : 'bg-white text-gray-700 border-gray-300 hover:border-amber-400'
              }`}>
              🌿 {s}
            </button>
          ))}
        </div>
      )}

      {/* Active filters bar */}
      {(category || gender || scentFamily) && (
        <div className="flex items-center gap-2 mb-4 text-sm text-gray-600">
          <span>Filters:</span>
          {category && <span className="bg-purple-100 text-purple-800 px-2 py-0.5 rounded-full text-xs">{category}</span>}
          {gender && <span className="bg-blue-100 text-blue-800 px-2 py-0.5 rounded-full text-xs">{gender}</span>}
          {scentFamily && <span className="bg-amber-100 text-amber-800 px-2 py-0.5 rounded-full text-xs">{scentFamily}</span>}
          <button onClick={clearAll} className="text-purple-600 hover:underline text-xs ml-2">Clear all</button>
        </div>
      )}

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
                <div className="flex items-center gap-1 mt-0.5">
                  {p.gender && <span className="text-xs text-gray-400">{GENDER_ICONS[p.gender] || p.gender}</span>}
                  {p.scent_family && <span className="text-xs text-gray-400">· {p.scent_family}</span>}
                </div>
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
