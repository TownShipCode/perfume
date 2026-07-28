import { Link } from 'react-router-dom';

export default function Landing() {
  return (
    <div>
      <section className="text-center py-24 px-4 bg-gradient-to-b from-purple-50 to-white">
        <h1 className="text-5xl font-bold text-gray-900 mb-4">Zen Fragrances</h1>
        <p className="text-xl text-gray-600 max-w-xl mx-auto mb-8">
          Premium perfume oils for resellers. 99+ fragrances. Same price for everyone.
        </p>
        <div className="flex gap-4 justify-center">
          <Link to="/catalogue" className="bg-purple-700 text-white px-8 py-3 rounded-xl font-medium text-lg hover:bg-purple-800 transition-colors">
            Browse Catalogue
          </Link>
          <Link to="/register/agent" className="border-2 border-purple-700 text-purple-700 px-8 py-3 rounded-xl font-medium text-lg hover:bg-purple-50 transition-colors">
            Become an Agent
          </Link>
        </div>
      </section>

      <section className="max-w-5xl mx-auto py-16 px-4 grid grid-cols-1 md:grid-cols-4 gap-8 text-center">
        {[
          { title: '99+ Fragrances', desc: 'Woody, floral, oriental, fresh — a scent for every customer.' },
          { title: 'Nationwide Delivery', desc: 'R65 flat rate. Free shipping on orders over R2000.' },
          { title: 'Agent Program', desc: 'Earn 5% commission on every order from your agents.' },
          { title: 'WhatsApp Ordering', desc: 'Order in seconds via WhatsApp. No website needed.' },
        ].map(f => (
          <div key={f.title} className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
            <h3 className="font-semibold text-lg mb-2">{f.title}</h3>
            <p className="text-sm text-gray-500">{f.desc}</p>
          </div>
        ))}
      </section>

      <section className="bg-purple-700 text-white py-16 text-center">
        <h2 className="text-3xl font-bold mb-4">Ready to start selling?</h2>
        <p className="text-purple-200 mb-6">Order via WhatsApp or browse our online catalogue.</p>
        <Link to="/register" className="bg-white text-purple-700 px-8 py-3 rounded-xl font-medium text-lg hover:bg-purple-50 transition-colors">
          Register Now
        </Link>
      </section>
    </div>
  );
}
