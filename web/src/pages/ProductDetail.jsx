import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { api } from '../api';

export default function ProductDetail() {
  const { id } = useParams();
  const [product, setProduct] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api(`/api/products/${id}`).then(setProduct).catch(() => setProduct(null)).finally(() => setLoading(false));
  }, [id]);

  if (loading) return <div className="max-w-3xl mx-auto px-4 py-12 text-center text-gray-500">Loading...</div>;
  if (!product) return <div className="max-w-3xl mx-auto px-4 py-12 text-center text-gray-500">Product not found.</div>;

  const whatsappLink = `https://wa.me/27123456789?text=order%20${encodeURIComponent(product.name)}`;

  return (
    <div className="max-w-3xl mx-auto px-4 py-8">
      <Link to="/catalogue" className="text-purple-700 text-sm mb-4 inline-block">&larr; Back to Catalogue</Link>
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
        <div className="aspect-video bg-gray-100 flex items-center justify-center text-6xl">
          {product.image_url ? <img src={product.image_url} alt={product.name} className="w-full h-full object-cover" /> : '🫧'}
        </div>
        <div className="p-6">
          <h1 className="text-2xl font-bold">{product.name}</h1>
          <p className="text-3xl font-bold text-purple-700 mt-2">R{product.price}</p>
          {product.scent_family && <p className="text-sm text-gray-500 mt-1">{product.gender} &middot; {product.scent_family}</p>}
          {product.top_notes && <p className="text-sm text-gray-500 mt-1">Top Notes: {product.top_notes}</p>}
          {product.description && <p className="mt-4 text-gray-700">{product.description}</p>}
          {product.stock_quantity != null && (
            <p className={`mt-3 text-sm font-medium ${product.stock_quantity > 5 ? 'text-green-600' : product.stock_quantity > 0 ? 'text-amber-600' : 'text-red-600'}`}>
              {product.stock_quantity > 0 ? `📦 ${product.stock_quantity} in stock` : '❌ Out of stock'}
            </p>
          )}
          <a href={whatsappLink} target="_blank" rel="noopener noreferrer"
            className="mt-6 inline-block bg-green-600 text-white px-8 py-3 rounded-xl font-medium text-lg hover:bg-green-700 transition-colors">
            📱 Order via WhatsApp
          </a>
        </div>
      </div>
    </div>
  );
}
