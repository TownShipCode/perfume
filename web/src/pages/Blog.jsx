import { Link } from 'react-router-dom';

const ARTICLES = [
  {
    slug: 'best-perfume-dupes-south-africa-2026',
    title: 'Best Perfume Dupes in South Africa — 2026 Guide',
    date: '2026-07-15',
    excerpt: 'Discover the top designer-inspired fragrances available in South Africa. From Creed Aventus to Baccarat Rouge 540 — we cover the best alternatives that smell identical and last longer.',
    tags: ['Fragrance Guide', 'Dupes'],
  },
  {
    slug: 'how-to-start-perfume-business-whatsapp',
    title: 'How to Start a Perfume Business from Your Phone',
    date: '2026-07-10',
    excerpt: 'No website, no shop, no inventory risk. Learn how to start selling perfumes using only WhatsApp — from choosing products to finding your first customers.',
    tags: ['Business', 'Agents'],
  },
  {
    slug: 'edt-vs-edp-vs-parfum',
    title: 'EDT vs EDP vs Parfum — What\'s the Difference?',
    date: '2026-07-05',
    excerpt: 'Understanding fragrance concentrations helps you sell better. Learn the differences between Eau de Toilette, Eau de Parfum, and Parfum — and what your customers prefer.',
    tags: ['Education', 'Fragrance Guide'],
  },
  {
    slug: 'top-10-mens-fragrances-2026',
    title: 'Top 10 Men\'s Fragrances Trending in South Africa',
    date: '2026-06-28',
    excerpt: 'From fresh citrus to deep oud — these are the 10 men\'s fragrances South African customers are buying most in 2026.',
    tags: ['Men', 'Trends'],
  },
  {
    slug: 'why-buy-wholesale-perfume',
    title: 'Why Buying Wholesale Perfume is Smarter Than Retail',
    date: '2026-06-20',
    excerpt: 'Wholesale perfumes offer the same quality at a fraction of the price. Here\'s why more South Africans are switching to wholesale fragrance suppliers.',
    tags: ['Wholesale', 'Education'],
  },
];

export default function Blog() {
  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold mb-2">Blog</h1>
      <p className="text-gray-500 mb-8">Fragrance guides, business tips, and industry insights.</p>

      <div className="grid gap-6">
        {ARTICLES.map(article => (
          <Link key={article.slug} to={`/blog/${article.slug}`}
            className="bg-white rounded-xl border border-gray-100 shadow-sm p-5 hover:shadow-md hover:border-purple-200 transition-all group">
            <div className="flex flex-wrap gap-2 mb-2">
              {article.tags.map(tag => (
                <span key={tag} className="text-xs bg-purple-50 text-purple-700 px-2 py-0.5 rounded-full">{tag}</span>
              ))}
            </div>
            <h2 className="text-lg font-semibold group-hover:text-purple-700 transition-colors">{article.title}</h2>
            <p className="text-sm text-gray-500 mt-1">{article.date}</p>
            <p className="text-gray-600 mt-2 text-sm leading-relaxed">{article.excerpt}</p>
            <span className="text-purple-600 text-sm font-medium mt-2 inline-block group-hover:underline">Read more →</span>
          </Link>
        ))}
      </div>
    </div>
  );
}
