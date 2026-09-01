import { Link } from 'react-router-dom';
import { useCart } from '../useCart';
import { useConfig, shippingFee, freeThreshold } from '../useConfig';
import { productEmoji } from '../productEmoji';

export default function Cart() {
  const { items, updateQty, removeItem, total, count, clearCart } = useCart();
  const config = useConfig();
  const shipFee = shippingFee(config);
  const threshold = freeThreshold(config);
  const shipping = total >= threshold ? 0 : shipFee;

  if (items.length === 0) return (
    <div className="max-w-2xl mx-auto px-4 py-16 text-center">
      <p className="text-5xl mb-4 font-serif font-bold text-purple-700">0</p>
      <h1 className="text-2xl font-bold mb-2">Your cart is empty</h1>
      <p className="text-gray-500 mb-6">Browse our catalogue and add some fragrances.</p>
      <Link to="/catalogue" className="bg-purple-700 text-white px-6 py-3 rounded-xl font-medium hover:bg-purple-800 transition-colors inline-block">
        Browse Catalogue
      </Link>
    </div>
  );

  return (
    <div className="max-w-2xl mx-auto px-4 py-8">
      <h1 className="text-2xl font-bold mb-6">Your Cart ({count} items)</h1>

      <div className="space-y-3 mb-8">
        {items.map(item => (
          <div key={item.id} className="bg-white rounded-xl border border-gray-100 shadow-sm p-4 flex gap-4 items-center">
            <div className="w-16 h-16 bg-gray-50 rounded-lg flex items-center justify-center text-2xl flex-shrink-0">
              {item.image_url ? <img src={item.image_url} alt={item.name} className="w-full h-full object-cover rounded-lg" /> : productEmoji(item)}
            </div>
            <div className="flex-1 min-w-0">
              <Link to={`/product/${item.id}`} className="font-medium text-sm hover:text-purple-700 truncate block">{item.name}</Link>
              <p className="text-purple-700 font-bold text-sm">R{item.price}</p>
            </div>
            <div className="flex items-center gap-1">
              <button onClick={() => updateQty(item.id, item.qty - 1)}
                className="w-7 h-7 rounded bg-gray-100 text-gray-600 font-bold hover:bg-gray-200">−</button>
              <span className="w-8 text-center text-sm font-medium">{item.qty}</span>
              <button onClick={() => updateQty(item.id, item.qty + 1)}
                className="w-7 h-7 rounded bg-purple-100 text-purple-700 font-bold hover:bg-purple-200">+</button>
            </div>
            <p className="font-semibold text-sm w-20 text-right">R{(parseFloat(item.price) * item.qty).toFixed(2)}</p>
            <button onClick={() => removeItem(item.id)} className="text-gray-400 hover:text-red-500 text-lg">&times;</button>
          </div>
        ))}
      </div>

      <div className="bg-white rounded-xl border border-gray-100 shadow-sm p-4 space-y-2 text-sm">
        <div className="flex justify-between"><span>Subtotal</span><span>R{total.toFixed(2)}</span></div>
        <div className="flex justify-between"><span>Delivery</span><span>{shipping === 0 ? <span className="text-green-600">FREE</span> : `R${shipping}.00`}</span></div>
        {shipping > 0 && (() => {
          const remaining = Math.max(0, threshold - total);
          const pct = Math.min(100, (total / threshold) * 100);
          return (
            <div className="pt-1">
              <div className="h-1.5 bg-purple-100 rounded-full overflow-hidden">
                <div className="h-full bg-purple-700 rounded-full transition-all" style={{ width: `${pct}%` }} />
              </div>
              <p className="text-xs text-gray-500 mt-2">
                {remaining > 0 ? `Add R${remaining.toFixed(0)} more for FREE delivery` : 'Free delivery unlocked'}
              </p>
            </div>
          );
        })()}
        <div className="flex justify-between font-bold text-lg pt-2 border-t"><span>Total</span><span className="text-purple-700">R{(total + shipping).toFixed(2)}</span></div>
      </div>

      <div className="flex gap-3 mt-6">
        <button onClick={clearCart} className="text-gray-500 hover:text-red-600 text-sm px-4 py-2">Clear cart</button>
        <Link to="/checkout" className="flex-1 bg-purple-700 text-white text-center px-6 py-3 rounded-xl font-medium hover:bg-purple-800 transition-colors">
          Proceed to Checkout
        </Link>
      </div>
    </div>
  );
}
