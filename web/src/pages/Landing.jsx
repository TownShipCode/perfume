import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { api } from '../api';
import { useCart } from '../useCart';
import { productEmoji } from '../productEmoji';
import Reviews from '../components/Reviews';

export default function Landing() {
  const [featured, setFeatured] = useState([]);
  const [productsState, setProductsState] = useState('loading'); // loading | ready | empty
  const { addItem, items } = useCart();

  // Product "display window": a tight set of 4 bestsellers; the full range
  // lives on /catalogue. Minimal text — the page's job is ordering.
  useEffect(() => {
    api('/api/products?page_size=4')
      .then(d => {
        const list = d.items || d.products || [];
        setFeatured(list);
        setProductsState(list.length ? 'ready' : 'empty');
      })
      .catch(() => setProductsState('empty'));
  }, []);

  return (
    <div>
      {/* Split hero card — left content, right featured bottle visual */}
      <section className="max-w-6xl mx-auto px-4 pt-10 pb-6">
        <div className="bg-gradient-to-br from-purple-700 via-purple-800 to-purple-950 rounded-3xl overflow-hidden shadow-xl">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-0 items-center">
            <div className="p-8 md:p-12 text-white">
              <span className="inline-block bg-white/15 text-purple-100 text-xs font-semibold px-3 py-1 rounded-full mb-5">
                Wholesale perfumes for resellers
              </span>
              <h1 className="text-4xl md:text-5xl font-bold mb-4">
                Inspired by your favourite designer scents 
              </h1>
              <p className="text-lg text-purple-200 max-w-md mb-6">
                Buy at wholesale, sell at your price. Starter pack at R420 excluding shipping, no minimum order — order on WhatsApp in seconds.
              </p>
              <div className="flex flex-wrap gap-2 mb-8">
                {['Inspired by your favourite designer scents', 'Oil-based · Alcohol-free', 'Long-lasting', 'Skin-friendly'].map(v => (
                  <span key={v} className="bg-white/10 text-purple-50 text-xs font-semibold px-3 py-1.5 rounded-full">{v}</span>
                ))}
              </div>
              <div className="flex gap-3 flex-wrap">
                <a href="#shop" className="bg-accent text-white px-7 py-3 rounded-xl font-bold text-lg hover:bg-accent-dark transition-colors shadow-lg">
                  Shop the collection
                </a>
                <Link to="/quick-order" className="bg-white/10 text-white px-7 py-3 rounded-xl font-medium text-lg hover:bg-white/20 transition-colors border border-white/20">
                  Quick Order
                </Link>
              </div>
            </div>
            {/* Featured bottle visual (emoji tile — on-brand, no asset needed) */}
            <div className="hidden md:flex items-center justify-center p-12 relative">
              <div className="absolute inset-0 opacity-25" style={{ background: 'radial-gradient(circle at 50% 60%, #34B7F1 0%, transparent 60%)' }} />
              <div className="relative text-center">
                <p className="text-7xl font-serif drop-shadow-lg">S</p>
                <p className="mt-3 text-xs uppercase tracking-widest text-purple-200">This month's pick</p>
                <p className="text-2xl font-bold text-white">SCANDAL</p>
                <p className="text-sm text-purple-300">by Jean Paul Gaultier</p>
                <p className="mt-2 inline-block bg-white text-purple-800 text-sm font-bold px-4 py-1.5 rounded-full">R30 wholesale</p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Product display window — real items, order-first */}
      <section id="shop" className="max-w-6xl mx-auto px-4 py-8">
        <div className="flex items-end justify-between mb-5">
          <h2 className="text-2xl md:text-3xl font-bold">Shop bestsellers</h2>
          <Link to="/catalogue" className="text-accent font-medium text-sm whitespace-nowrap">View all →</Link>
        </div>
        {productsState === 'loading' ? (
          <p className="text-gray-500 py-8 text-center">Loading fragrances…</p>
        ) : productsState === 'empty' ? (
          <div className="text-center py-8 border border-dashed border-gray-200 rounded-xl">
            <p className="text-gray-500 mb-3">Stock is being added — the full range is in the catalogue.</p>
            <Link to="/catalogue" className="inline-block bg-accent text-white px-6 py-2.5 rounded-lg font-medium hover:bg-accent-dark transition-colors">
              Browse the catalogue
            </Link>
          </div>
        ) : (
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
            {featured.map(p => {
              const inCart = items.find(i => i.id === p.id);
              return (
                <div key={p.id} className="bg-white rounded-xl border border-gray-100 overflow-hidden hover:shadow-md transition-shadow">
                  <Link to={`/product/${p.id}`}>
                    <div className="aspect-square bg-gray-100 flex items-center justify-center text-4xl">
                      {p.image_url ? <img src={p.image_url} alt={p.name} className="w-full h-full object-cover" /> : productEmoji(p)}
                    </div>
                    <div className="p-3">
                      <h3 className="font-medium text-sm truncate">{p.name}</h3>
                      <p className="text-ink font-bold mt-1">R{p.price}</p>
                    </div>
                  </Link>
                  <div className="px-3 pb-3">
                    <button onClick={() => addItem(p)}
                      className={`w-full text-xs font-medium py-1.5 rounded-lg transition-colors ${inCart ? 'bg-purple-100 text-purple-700' : 'bg-accent text-white hover:bg-accent-dark'}`}>
                      {inCart ? `In Cart (${inCart.qty})` : '+ Add to Cart'}
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </section>

      {/* Ordering steps — short, sell-focused */}
      <section className="max-w-5xl mx-auto py-8 px-4 grid grid-cols-1 sm:grid-cols-3 gap-6 text-center">
        {[
          { title: 'Pick a scent', desc: 'Add bottles to your cart.' },
          { title: 'Checkout', desc: 'Pay by card or EFT.' },
          { title: 'Delivered', desc: 'R65 flat · free over R2000.' },
        ].map(s => (
          <div key={s.title} className="bg-white rounded-xl p-5 shadow-sm border border-gray-100">
            <h3 className="font-semibold mb-1">{s.title}</h3>
            <p className="text-sm text-gray-500">{s.desc}</p>
          </div>
        ))}
      </section>

      {/* Brief social proof — short quotes, sells more than copy */}
      <Reviews />

      {/* Slim order-first closing band — registration is secondary */}
      <section className="bg-[#14171A] text-white py-12 px-4 text-center">
        <h2 className="text-2xl md:text-3xl font-bold mb-3">Order your first bottles</h2>
        <p className="text-purple-200 mb-6 max-w-lg mx-auto">R30 wholesale · R65 delivery · free over R2000.</p>
        <div className="flex gap-4 justify-center flex-wrap">
          <Link to="/catalogue" className="bg-accent text-white px-8 py-3 rounded-xl font-medium text-lg hover:bg-accent-dark transition-colors">
            Browse the collection
          </Link>
          <Link to="/register/agent" className="border border-white/30 text-white/80 px-8 py-3 rounded-xl font-medium text-lg hover:text-white hover:border-white transition-colors">
            Want to sell? Become an agent
          </Link>
        </div>
      </section>
    </div>
  );
}
