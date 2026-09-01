import { useState } from 'react';
import { Link } from 'react-router-dom';
import { api } from '../api';
import Reviews from '../components/Reviews';

export default function Landing() {
  const [email, setEmail] = useState('');
  const [subscribed, setSubscribed] = useState(false);
  const [subError, setSubError] = useState('');
  const [openFaq, setOpenFaq] = useState(null);

  const faqs = [
    { q: 'Are these real designer perfumes?', a: 'They are premium interpretations inspired by iconic designer scents — not fakes. Our fragrances are oil-based, alcohol-free, long-lasting and skin-friendly.' },
    { q: 'How do I order?', a: 'Two ways: browse this store and check out, or order on WhatsApp — just send a product name like "5 Rose Oud" and we\'ll confirm it for you.' },
    { q: 'How long does delivery take?', a: '3-5 working days nationwide via The Courier Guy. R65 flat rate, and FREE delivery on orders over R2,000.' },
    { q: 'Can I become an agent or reseller?', a: 'Yes — zero startup cost. Buy at wholesale, sell at your own price (~2×), and earn commission by building your team. No starter pack required.' },
    { q: 'Are they safe on my skin?', a: 'We use high-quality, IFRA-compliant fragrance oils that are skin-friendly and alcohol-free.' },
    { q: 'What if I don\'t like the scent?', a: 'Check our returns and exchange policy — we want you happy with your fragrance.' },
  ];

  async function handleSubscribe(e) {
    e.preventDefault();
    setSubError('');
    try {
      await api('/api/newsletter', { method: 'POST', body: JSON.stringify({ email }) });
      setSubscribed(true);
    } catch (err) {
      setSubError(err.message);
    }
  }

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
                Inspired by your favourite designer scents — <span className="text-purple-200">not a dupe</span>.
              </h1>
              <p className="text-lg text-purple-200 max-w-md mb-6">
                Buy at wholesale, sell at your price. No starter pack, no minimum order — order on WhatsApp in seconds.
              </p>
              <div className="flex flex-wrap gap-2 mb-8">
                {['Inspired by, not a dupe', 'Oil-based · Alcohol-free', 'Long-lasting', 'Skin-friendly'].map(v => (
                  <span key={v} className="bg-white/10 text-purple-50 text-xs font-semibold px-3 py-1.5 rounded-full">{v}</span>
                ))}
              </div>
              <div className="flex gap-3 flex-wrap">
                <Link to="/catalogue" className="bg-white text-purple-800 px-7 py-3 rounded-xl font-bold text-lg hover:bg-purple-50 transition-colors shadow-lg">
                  Browse Catalogue
                </Link>
                <Link to="/quick-order" className="bg-white/10 text-white px-7 py-3 rounded-xl font-medium text-lg hover:bg-white/20 transition-colors border border-white/20">
                  Quick Order
                </Link>
                <Link to="/register/agent" className="text-purple-200 px-2 py-3 font-medium text-lg hover:text-white transition-colors">
                  Become an Agent →
                </Link>
              </div>
            </div>
            {/* Featured bottle visual (emoji tile — on-brand, no asset needed) */}
            <div className="hidden md:flex items-center justify-center p-12 relative">
              <div className="absolute inset-0 opacity-20" style={{ background: 'radial-gradient(circle at 50% 60%, #c4b5fd 0%, transparent 60%)' }} />
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

      <section className="max-w-5xl mx-auto py-16 px-4 grid grid-cols-1 md:grid-cols-4 gap-8 text-center">
        {[
          { title: '99+ Fragrances', desc: 'Woody, floral, oriental, fresh — a scent for every customer.' },
          { title: 'Nationwide Delivery', desc: 'R65 flat rate. Free shipping on orders over R2000.' },
          { title: 'Agent Program', desc: 'Buy wholesale, sell at 2×. Earn 5% from your team.' },
          { title: 'WhatsApp Ordering', desc: 'Order in seconds via WhatsApp. No website needed.' },
        ].map(f => (
          <div key={f.title} className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
            <h3 className="font-semibold text-lg mb-2">{f.title}</h3>
            <p className="text-sm text-gray-500">{f.desc}</p>
          </div>
        ))}
      </section>

      {/* Why Zen — brand story (Fragrance Passion / Guerlain style) */}
      <section className="bg-white py-16 px-4 border-t border-gray-100">
        <div className="max-w-4xl mx-auto text-center">
          <h2 className="text-3xl font-bold mb-6">Why Zen Fragrances</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8 text-left">
            <div>
              <p className="text-3xl font-serif font-bold text-purple-700">1</p>
              <h3 className="font-semibold mb-1">Oil-based, not watered down</h3>
              <p className="text-sm text-gray-500">High fragrance dosage, alcohol-free, and built to last. Inspired by your favourite designer scents — not a dupe.</p>
            </div>
            <div>
              <p className="text-3xl font-serif font-bold text-purple-700">2</p>
              <h3 className="font-semibold mb-1">Built for resellers</h3>
              <p className="text-sm text-gray-500">No starter pack, no minimum order. Buy wholesale, set your own retail price, and earn 5% from agents you recruit.</p>
            </div>
            <div>
              <p className="text-3xl font-serif font-bold text-purple-700">3</p>
              <h3 className="font-semibold mb-1">WhatsApp-native</h3>
              <p className="text-sm text-gray-500">Order in seconds on WhatsApp. No apps, no portals — just message us and we confirm your order.</p>
            </div>
          </div>
        </div>
      </section>

      {/* Category cards (Guerlain / Acqua di Parma style) */}
      <section className="max-w-5xl mx-auto pb-16 px-4 grid grid-cols-2 md:grid-cols-4 gap-4">
        <Link to="/catalogue?gender=men" className="bg-gradient-to-br from-purple-100 to-purple-50 rounded-xl p-6 text-center hover:shadow-md transition-all group">
          <span className="text-3xl font-serif font-bold text-purple-700">M</span>
          <h3 className="font-semibold mt-2 group-hover:text-purple-700">Men's Scents</h3>
          <p className="text-xs text-gray-500 mt-1">Bold, fresh &amp; confident</p>
        </Link>
        <Link to="/catalogue?gender=women" className="bg-gradient-to-br from-purple-100 to-purple-50 rounded-xl p-6 text-center hover:shadow-md transition-all group">
          <span className="text-3xl font-serif font-bold text-purple-700">W</span>
          <h3 className="font-semibold mt-2 group-hover:text-purple-700">Women's Scents</h3>
          <p className="text-xs text-gray-500 mt-1">Elegant, floral &amp; warm</p>
        </Link>
        <Link to="/scent-finder" className="bg-gradient-to-br from-purple-50 to-purple-100 rounded-xl p-6 text-center hover:shadow-md transition-all group">
          <span className="text-3xl font-serif font-bold text-purple-700">?</span>
          <h3 className="font-semibold mt-2 group-hover:text-purple-700">Find Your Scent</h3>
          <p className="text-xs text-gray-500 mt-1">A 30-second quiz</p>
        </Link>
        <Link to="/register/agent" className="bg-gradient-to-br from-green-100 to-green-50 rounded-xl p-6 text-center hover:shadow-md transition-all group">
          <span className="text-3xl font-serif font-bold text-green-700">A</span>
          <h3 className="font-semibold mt-2 group-hover:text-green-700">Become an Agent</h3>
          <p className="text-xs text-gray-500 mt-1">Sell at 2× wholesale</p>
        </Link>
      </section>

      <section className="max-w-5xl mx-auto pb-16 px-4 grid grid-cols-1 md:grid-cols-3 gap-6">
        <Link to="/quick-order" className="bg-white rounded-xl p-6 shadow-sm border border-purple-100 hover:border-purple-300 hover:shadow-md transition-all text-center group">
          <span className="text-3xl font-serif font-bold text-purple-700">Q</span>
          <h3 className="font-semibold mt-2 group-hover:text-purple-700">Quick Order</h3>
          <p className="text-sm text-gray-500 mt-1">Add quantities and send your order in one tap</p>
        </Link>
        <Link to="/blog" className="bg-white rounded-xl p-6 shadow-sm border border-purple-100 hover:border-purple-300 hover:shadow-md transition-all text-center group">
          <span className="text-3xl font-serif font-bold text-purple-700">B</span>
          <h3 className="font-semibold mt-2 group-hover:text-purple-700">Fragrance Blog</h3>
          <p className="text-sm text-gray-500 mt-1">Guides, tips, and industry insights for resellers</p>
        </Link>
        <Link to="/agents" className="bg-white rounded-xl p-6 shadow-sm border border-purple-100 hover:border-purple-300 hover:shadow-md transition-all text-center group">
          <span className="text-3xl font-serif font-bold text-purple-700">A</span>
          <h3 className="font-semibold mt-2 group-hover:text-purple-700">Find an Agent</h3>
          <p className="text-sm text-gray-500 mt-1">Find a Zen Fragrances agent in your area</p>
        </Link>
      </section>

      {/* Reviews wall (Fragrance Passion style) */}
      <Reviews />

      <section className="bg-white py-16 px-4">
        <div className="max-w-2xl mx-auto">
          <h2 className="text-2xl font-bold text-center mb-8">Frequently asked questions</h2>
          <div className="space-y-3">
            {faqs.map((faq, i) => (
              <div key={i} className="bg-gray-50 rounded-xl border border-gray-100 overflow-hidden">
                <button
                  onClick={() => setOpenFaq(openFaq === i ? null : i)}
                  className="w-full px-6 py-4 text-left flex justify-between items-center hover:bg-gray-100 transition-colors">
                  <span className="font-medium text-gray-800 pr-4">{faq.q}</span>
                  <span className={`text-purple-500 transition-transform flex-shrink-0 ${openFaq === i ? 'rotate-45' : ''}`}>＋</span>
                </button>
                {openFaq === i && (
                  <div className="px-6 pb-4 text-sm text-gray-600 leading-relaxed">{faq.a}</div>
                )}
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="bg-purple-50 py-16 px-4">
        <div className="max-w-lg mx-auto text-center">
          <h2 className="text-2xl font-bold mb-2">Get launch updates</h2>
          <p className="text-gray-500 text-sm mb-6">New fragrances, deals and restock alerts straight to your inbox. No spam.</p>
          {subscribed ? (
            <p className="text-green-600 font-medium">Thanks! You're on the list.</p>
          ) : (
            <form onSubmit={handleSubscribe} className="flex flex-col sm:flex-row gap-2">
              <input
                type="email"
                required
                value={email}
                onChange={e => setEmail(e.target.value)}
                placeholder="you@email.com"
                className="flex-1 border border-gray-300 rounded-lg px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-purple-300"
              />
              <button type="submit" className="bg-purple-700 text-white px-6 py-2.5 rounded-lg font-medium hover:bg-purple-800 transition-colors">
                Sign Up
              </button>
            </form>
          )}
          {subError && <p className="text-red-600 text-sm mt-3">{subError}</p>}
        </div>
      </section>

      <section className="bg-purple-700 text-white py-16 text-center">
        <h2 className="text-3xl font-bold mb-4">Ready to start selling?</h2>
        <p className="text-purple-200 mb-6">Join as an agent, buy at wholesale, and sell at your own price.</p>
        <div className="flex gap-4 justify-center flex-wrap">
          <Link to="/register/agent" className="bg-white text-purple-700 px-8 py-3 rounded-xl font-medium text-lg hover:bg-purple-50 transition-colors">
            Become an Agent
          </Link>
          <Link to="/catalogue" className="border-2 border-white text-white px-8 py-3 rounded-xl font-medium text-lg hover:bg-purple-600 transition-colors">
            Browse Catalogue
          </Link>
        </div>
      </section>
    </div>
  );
}
