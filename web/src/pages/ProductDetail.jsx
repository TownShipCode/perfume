import { useState, useEffect } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { api } from '../api';
import { useCart } from '../useCart';
import { productEmoji } from '../productEmoji';

const GENDER_LABELS = { men: 'For Men', women: 'For Women', unisex: 'Unisex' };

const TRUST_BADGES = ['🌱 Vegan', '🐰 Cruelty Free', '🚫 Alcohol-Free', '💧 Oil-Based', '🔁 Recyclable'];

function stockBadge(qty) {
  if (qty == null) return null;
  if (qty <= 0) return { label: 'Out of stock', css: 'bg-red-100 text-red-800' };
  if (qty <= 5) return { label: `Only ${qty} left`, css: 'bg-purple-100 text-purple-800' };
  return { label: `${qty} in stock`, css: 'bg-green-100 text-green-800' };
}

export default function ProductDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [product, setProduct] = useState(null);
  const [loading, setLoading] = useState(true);
  const { addItem, items } = useCart();
  const inCart = items.find(i => i.id === product?.id);

  useEffect(() => {
    api(`/api/products/${id}`).then(setProduct).catch(() => setProduct(null)).finally(() => setLoading(false));
  }, [id]);

  if (loading) return <div className="max-w-3xl mx-auto px-4 py-12 text-center text-gray-500">Loading...</div>;
  if (!product) return <div className="max-w-3xl mx-auto px-4 py-12 text-center text-gray-500">Product not found.</div>;

  const stock = stockBadge(product.stock_quantity);
  const WA_NUMBER = import.meta.env.VITE_WHATSAPP_NUMBER || '27123456789';
  const whatsappLink = `https://wa.me/${WA_NUMBER}?text=order%20${encodeURIComponent(product.name)}`;

  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      <Link to="/catalogue" className="text-purple-700 text-sm mb-4 inline-block hover:underline">&larr; Back to Catalogue</Link>

      <div className="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden">
        <div className="aspect-[3/2] bg-gradient-to-br from-purple-50 to-purple-100 flex items-center justify-center text-8xl">
          {product.image_url
            ? <img src={product.image_url} alt={product.name} className="w-full h-full object-contain p-4" />
            : productEmoji(product)}
        </div>

        <div className="p-6 md:p-8">
          <div className="flex flex-wrap items-start justify-between gap-3 mb-4">
            <div>
              <h1 className="text-2xl md:text-3xl font-bold text-gray-900">{product.name}</h1>
              <p className="text-sm text-gray-500 mt-1">Inspired by your favourite designer scent — not a dupe.</p>
              {product.categories?.length > 0 && (
                <p className="text-sm text-gray-500 mt-1">
                  {product.categories.map(c => (
                    <span key={c} className="inline-block bg-gray-100 text-gray-600 px-2 py-0.5 rounded-full text-xs mr-1">{c}</span>
                  ))}
                </p>
              )}
            </div>
            <p className="text-3xl font-bold text-purple-700">R{product.price}</p>
          </div>

          <div className="flex flex-wrap gap-2 mb-5">
            {product.gender && (
              <span className="inline-flex items-center gap-1 px-3 py-1 rounded-full text-xs font-medium bg-purple-50 text-purple-700 border border-purple-200">
                {GENDER_LABELS[product.gender] || product.gender}
              </span>
            )}
            {product.scent_family && (
              <span className="inline-flex items-center gap-1 px-3 py-1 rounded-full text-xs font-medium bg-purple-50 text-purple-700 border border-purple-200">
                {product.scent_family}
              </span>
            )}
            {stock && (
              <span className={`inline-flex items-center gap-1 px-3 py-1 rounded-full text-xs font-medium ${stock.css}`}>
                {stock.label}
              </span>
            )}
          </div>

          {(product.scent_family || product.top_notes) && (
            <div className="bg-gradient-to-r from-purple-50 to-purple-100 rounded-xl p-4 mb-5 border border-purple-100">
              <h3 className="text-sm font-semibold text-purple-800 mb-2">Scent Profile</h3>
              <div className="grid grid-cols-2 gap-3 text-sm">
                {product.gender && <div><span className="text-gray-500">Gender</span><p className="font-medium text-gray-800">{product.gender}</p></div>}
                {product.scent_family && <div><span className="text-gray-500">Scent Family</span><p className="font-medium text-gray-800">{product.scent_family}</p></div>}
                {product.top_notes && <div className="col-span-2"><span className="text-gray-500">Top Notes</span><p className="font-medium text-gray-800">{product.top_notes}</p></div>}
              </div>
            </div>
          )}

          {/* Trust badges — matches Forever Fragrances' clean-label row */}
          <div className="flex flex-wrap gap-2 mb-5">
            {TRUST_BADGES.map(b => (
              <span key={b} className="inline-flex items-center gap-1 text-xs font-medium text-gray-600 bg-gray-50 border border-gray-200 px-2.5 py-1 rounded-full">
                {b}
              </span>
            ))}
          </div>

          {product.description && (
            <div className="mb-6">
              <h3 className="text-sm font-semibold text-gray-700 mb-1">Description</h3>
              <p className="text-gray-600 leading-relaxed">{product.description}</p>
            </div>
          )}

          <div className="flex flex-wrap gap-3 pt-2">
            <button onClick={() => addItem(product)}
              className="inline-flex items-center gap-2 bg-purple-600 text-white px-6 py-3 rounded-xl font-medium hover:bg-purple-700 transition-colors">
              {inCart ? `Add Another (${inCart.qty} in cart)` : 'Add to Cart'}
            </button>
            <button onClick={() => { addItem(product); navigate('/checkout'); }}
              className="inline-flex items-center gap-2 bg-purple-900 text-white px-6 py-3 rounded-xl font-medium hover:bg-purple-950 transition-colors">
              Buy It Now
            </button>
            <a href={whatsappLink} target="_blank" rel="noopener noreferrer"
              className="inline-flex items-center gap-2 bg-green-600 text-white px-6 py-3 rounded-xl font-medium hover:bg-green-700 transition-colors">
              Order via WhatsApp
            </a>
          </div>
          <p className="text-xs text-gray-400 mt-4">Prices shown are wholesale. Agents set their own retail prices (suggested: 2× wholesale).</p>
        </div>
      </div>
    </div>
  );
}
