import React, { useEffect, useState } from 'react';

import { dashboardApi } from './api.js';

const emptyProduct = {
  product_number: 1,
  name: '',
  price: '0.00',
  image_url: '',
  description: '',
  is_active: true,
  keywords: '',
};

const emptyAddress = { area: '', street: '', city: '' };

function loadSetting(key, fallback) {
  try { return localStorage.getItem(key) || fallback; } catch { return fallback; }
}
function saveSetting(key, value) {
  try { localStorage.setItem(key, value); } catch { /* noop */ }
}

const PROD_URL = 'https://biomed-production.up.railway.app';

export default function App() {
  const [apiKey, setApiKey] = useState(() => loadSetting('biomed_api_key', ''));
  const [baseUrl, setBaseUrl] = useState(() => loadSetting('biomed_base_url', PROD_URL));
  const [orders, setOrders] = useState([]);
  const [selectedOrder, setSelectedOrder] = useState(null);
  const [selectedOrderPreview, setSelectedOrderPreview] = useState(null);
  const [customers, setCustomers] = useState([]);
  const [products, setProducts] = useState([]);
  const [selectedCustomer, setSelectedCustomer] = useState(null);
  const [customerOrders, setCustomerOrders] = useState([]);
  const [templates, setTemplates] = useState([]);
  const [selectedTemplateKey, setSelectedTemplateKey] = useState('');
  const [templateBody, setTemplateBody] = useState('');
  const [productForm, setProductForm] = useState(emptyProduct);
  const [editingProductId, setEditingProductId] = useState(null);
  const [addressForm, setAddressForm] = useState(emptyAddress);
  const [statusFilter, setStatusFilter] = useState('');
  const [forwardStatusFilter, setForwardStatusFilter] = useState('');
  const [message, setMessage] = useState('');

  async function loadAll() {
    try {
      const [ordersResponse, customersResponse, productsResponse, templatesResponse] = await Promise.all([
        dashboardApi.getOrders(apiKey, baseUrl, statusFilter, forwardStatusFilter),
        dashboardApi.getCustomers(apiKey, baseUrl),
        dashboardApi.getProducts(apiKey, baseUrl),
        dashboardApi.getTemplates(apiKey, baseUrl),
      ]);
      setOrders(ordersResponse.items);
      setCustomers(customersResponse.items);
      setProducts(productsResponse.items);
      setTemplates(templatesResponse.items);
      if (!selectedTemplateKey && templatesResponse.items.length > 0) {
        setSelectedTemplateKey(templatesResponse.items[0].template_key);
        setTemplateBody(templatesResponse.items[0].body);
      }
      setMessage('Data refreshed.');
    } catch (error) {
      setMessage(error.message);
    }
  }

  async function loadOrderDetail(orderId) {
    try {
      const response = await dashboardApi.getOrder(orderId, apiKey, baseUrl);
      setSelectedOrder(response.item);
      setSelectedOrderPreview(response.manufacturer_forward_preview || null);
    } catch (error) {
      setMessage(error.message);
    }
  }

  useEffect(() => {
    loadAll();
  }, [statusFilter, forwardStatusFilter]);

  useEffect(() => {
    const activeTemplate = templates.find((template) => template.template_key === selectedTemplateKey);
    if (activeTemplate) {
      setTemplateBody(activeTemplate.body);
    }
  }, [selectedTemplateKey, templates]);

  async function loadCustomerOrders(phoneNumber) {
    try {
      const response = await dashboardApi.getCustomerOrders(phoneNumber, apiKey, baseUrl);
      setSelectedCustomer(response.customer);
      setCustomerOrders(response.items);
      setAddressForm({
        area: response.customer.area || '',
        street: response.customer.street || '',
        city: response.customer.city || '',
      });
    } catch (error) {
      setMessage(error.message);
    }
  }

  async function submitProduct(event) {
    event.preventDefault();
    const payload = {
      ...productForm,
      price: productForm.price,
      product_number: Number(productForm.product_number),
      keywords: productForm.keywords.split(',').map((keyword) => keyword.trim()).filter(Boolean),
    };
    try {
      if (editingProductId) {
        await dashboardApi.updateProduct(editingProductId, payload, apiKey, baseUrl);
        setMessage('Product updated.');
        // stay in edit mode so the user can see their changes persisted
      } else {
        await dashboardApi.createProduct(payload, apiKey, baseUrl);
        setMessage('Product created.');
        setProductForm(emptyProduct);
        setEditingProductId(null);
      }
      await loadAll();
    } catch (error) {
      setMessage(error.message);
    }
  }

  async function removeProduct(id) {
    try {
      await dashboardApi.deleteProduct(id, apiKey, baseUrl);
      setMessage('Product deleted.');
      await loadAll();
    } catch (error) {
      setMessage(error.message);
    }
  }

  async function changeOrderStatus(orderId, status) {
    try {
      await dashboardApi.updateOrderStatus(orderId, status, apiKey, baseUrl);
      setMessage(`Order ${orderId} updated to ${status}.`);
      await loadAll();
      if (selectedOrder?.id === orderId) {
        await loadOrderDetail(orderId);
      }
      if (selectedCustomer) {
        await loadCustomerOrders(selectedCustomer.phone_number);
      }
    } catch (error) {
      setMessage(error.message);
    }
  }

  async function confirmOrder(orderId) {
    try {
      await dashboardApi.confirmOrder(orderId, apiKey, baseUrl);
      setMessage(`Order ${orderId} confirmed.`);
      await loadAll();
      if (selectedOrder?.id === orderId) {
        await loadOrderDetail(orderId);
      }
    } catch (error) {
      setMessage(error.message);
    }
  }

  async function forwardOrder(order) {
    try {
      const shouldRetry = Boolean(order.forward_delivery_status);
      const response = await dashboardApi.forwardOrder(order.id, apiKey, baseUrl, shouldRetry);
      if (response.action === 'forward_skipped') {
        setMessage(`Order ${order.id} was already forwarded${response.recipient ? ` to ${response.recipient}` : ''}. Use retry to resend.`);
      } else {
        setMessage(`Order ${order.id} forwarded to ${response.recipient} (${response.delivery.status}).`);
      }
      await loadAll();
      await loadOrderDetail(order.id);
      if (selectedCustomer) {
        await loadCustomerOrders(selectedCustomer.phone_number);
      }
    } catch (error) {
      setMessage(error.message);
    }
  }

  async function saveAddress(event) {
    event.preventDefault();
    if (!selectedCustomer) {
      return;
    }
    try {
      await dashboardApi.updateCustomerAddress(selectedCustomer.phone_number, addressForm, apiKey, baseUrl);
      setMessage('Customer address updated.');
      await loadAll();
      await loadCustomerOrders(selectedCustomer.phone_number);
    } catch (error) {
      setMessage(error.message);
    }
  }

  async function saveTemplate(event) {
    event.preventDefault();
    if (!selectedTemplateKey) {
      return;
    }
    try {
      await dashboardApi.updateTemplate(selectedTemplateKey, templateBody, apiKey, baseUrl);
      setMessage(`Template ${selectedTemplateKey} updated.`);
      await loadAll();
    } catch (error) {
      setMessage(error.message);
    }
  }

  function beginEditProduct(product) {
    setEditingProductId(product.id);
    const kw = product.keywords || [];
    setProductForm({
      product_number: product.product_number,
      name: product.name || '',
      price: product.price != null ? String(product.price) : '0.00',
      image_url: product.image_url || '',
      description: product.description || '',
      is_active: Boolean(product.is_active),
      keywords: Array.isArray(kw) ? kw.join(', ') : '',
    });
    setMessage('Editing product. Update keywords and save.');
  }

  return (
    <div className="app-shell">
      <aside className="control-rail">
        <h1>BioMed Control Desk</h1>
        <p>Orders, products, and customer addresses in one operational board.</p>

        <label>
          API base URL
          <input value={baseUrl} onChange={(event) => { setBaseUrl(event.target.value); saveSetting('biomed_base_url', event.target.value); }} />
        </label>

        <label>
          Dashboard API key
          <input type="password" value={apiKey} onChange={(event) => { setApiKey(event.target.value); saveSetting('biomed_api_key', event.target.value); }} />
        </label>

        <button onClick={loadAll}>Refresh board</button>

        <label>
          Order status filter
          <select value={statusFilter} onChange={(event) => setStatusFilter(event.target.value)}>
            <option value="">All</option>
            <option value="pending">Pending</option>
            <option value="pop_received">POP received</option>
            <option value="confirmed">Confirmed</option>
          </select>
        </label>

        <label>
          Forwarding filter
          <select value={forwardStatusFilter} onChange={(event) => setForwardStatusFilter(event.target.value)}>
            <option value="">All</option>
            <option value="dry_run">Dry run</option>
            <option value="sent">Sent</option>
            <option value="failed">Failed</option>
            <option value="skipped">Skipped</option>
          </select>
        </label>

        <div className="status-card">{message || 'Ready.'}</div>
      </aside>

      <main className="board-grid">
        <section className="panel panel-orders">
          <header><h2>Orders</h2></header>
          <div className="table-wrap">
            <table>
              <thead>
                <tr><th>#</th><th>Customer</th><th>Status</th><th>Forwarding</th><th>Total</th><th>Actions</th></tr>
              </thead>
              <tbody>
                {orders.map((order) => (
                  <tr key={order.id}>
                    <td>{order.order_number}</td>
                    <td>{order.phone_number}</td>
                    <td>{order.status}</td>
                    <td>{formatForwardingState(order)}</td>
                    <td>R{order.total}</td>
                    <td className="actions">
                      <button onClick={() => loadOrderDetail(order.id)}>Open</button>
                      <button onClick={() => confirmOrder(order.id)}>Confirm</button>
                      <button onClick={() => forwardOrder(order)}>{order.forward_delivery_status ? 'Retry' : 'Forward'}</button>
                      <button onClick={() => changeOrderStatus(order.id, 'shipped')}>Ship</button>
                      <button onClick={() => changeOrderStatus(order.id, 'delivered')}>Deliver</button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {selectedOrder && (
            <div className="detail-panel order-detail-panel">
              <div className="detail-header">
                <h3>{selectedOrder.order_number}</h3>
                <button onClick={() => { setSelectedOrder(null); setSelectedOrderPreview(null); }}>Close</button>
              </div>
              <p>{selectedOrder.phone_number}</p>
              <p>{selectedOrder.full_address || 'No address saved yet.'}</p>
              <p>Forwarding: {formatForwardingState(selectedOrder)}</p>
              <p>Attempts: {selectedOrder.forward_attempts || 0}</p>
              <p>Message ID: {selectedOrder.forward_message_id || 'Not available'}</p>
              <p>Error: {selectedOrder.forward_error || 'None'}</p>
              <p>
                POP:{' '}
                {selectedOrder.pop_image_url ? (
                  <a href={selectedOrder.pop_image_url} target="_blank" rel="noreferrer">{selectedOrder.pop_image_url}</a>
                ) : (
                  'Not received'
                )}
              </p>
              <div className="message-preview">
                <strong>Manufacturer message</strong>
                <pre>{selectedOrderPreview?.message || 'No preview available.'}</pre>
              </div>
              <div className="message-preview">
                <strong>Order items</strong>
                <ul className="item-list">
                  {(selectedOrderPreview?.line_items || []).map((item) => (
                    <li key={`${item.product_id}-${item.product_name}`}>{item.quantity}x {item.product_name}</li>
                  ))}
                </ul>
              </div>
              <div className="message-preview">
                <strong>Manufacturer message preview</strong>
                <pre>{selectedOrderPreview?.message || 'No preview available.'}</pre>
              </div>
            </div>
          )}
        </section>

        <section className="panel panel-products">
          <header><h2>Products</h2></header>
          <form className="stack" onSubmit={submitProduct}>
            <input placeholder="Product number" value={productForm.product_number} onChange={(event) => setProductForm({ ...productForm, product_number: event.target.value })} />
            <input placeholder="Name" value={productForm.name} onChange={(event) => setProductForm({ ...productForm, name: event.target.value })} />
            <input placeholder="Price" value={productForm.price} onChange={(event) => setProductForm({ ...productForm, price: event.target.value })} />
            <input placeholder="Description (e.g., 1L bottle)" value={productForm.description} onChange={(event) => setProductForm({ ...productForm, description: event.target.value })} />
            <input placeholder="Image URL" value={productForm.image_url} onChange={(event) => setProductForm({ ...productForm, image_url: event.target.value })} />
            <input placeholder="Keywords comma-separated" value={productForm.keywords} onChange={(event) => setProductForm({ ...productForm, keywords: event.target.value })} />
            <label className="checkbox-row">
              <input type="checkbox" checked={productForm.is_active} onChange={(event) => setProductForm({ ...productForm, is_active: event.target.checked })} />
              Active
            </label>
            <button type="submit">{editingProductId ? 'Update product' : 'Create product'}</button>
          </form>

          <div className="card-list">
            {products.map((product) => (
              <article key={product.id} className="mini-card">
                <strong>{product.product_number}. {product.name}</strong>
                <span>R{product.price}</span>
                <span>{product.is_active ? 'Active' : 'Inactive'}</span>
                <div className="actions">
                  <button onClick={() => beginEditProduct(product)}>Edit</button>
                  <button onClick={() => removeProduct(product.id)}>Delete</button>
                </div>
              </article>
            ))}
          </div>
        </section>

        <section className="panel panel-customers">
          <header><h2>Customers</h2></header>
          <div className="customer-layout">
            <div className="card-list">
              {customers.map((customer) => (
                <article key={customer.id} className="mini-card">
                  <strong>{customer.name || customer.phone_number}</strong>
                  <span>{customer.phone_number}</span>
                  <span>{customer.order_count} orders</span>
                  <button onClick={() => loadCustomerOrders(customer.phone_number)}>Open</button>
                </article>
              ))}
            </div>

            {selectedCustomer && (
              <div className="detail-panel">
                <h3>{selectedCustomer.phone_number}</h3>
                <form className="stack" onSubmit={saveAddress}>
                  <input placeholder="Area" value={addressForm.area} onChange={(event) => setAddressForm({ ...addressForm, area: event.target.value })} />
                  <input placeholder="Street" value={addressForm.street} onChange={(event) => setAddressForm({ ...addressForm, street: event.target.value })} />
                  <input placeholder="City" value={addressForm.city} onChange={(event) => setAddressForm({ ...addressForm, city: event.target.value })} />
                  <button type="submit">Save address</button>
                </form>

                <ul className="history-list">
                  {customerOrders.map((order) => (
                    <li key={order.id}>{order.order_number} · {order.status} · R{order.total}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </section>

        <section className="panel panel-templates">
          <header><h2>Templates</h2></header>
          <form className="stack" onSubmit={saveTemplate}>
            <select value={selectedTemplateKey} onChange={(event) => setSelectedTemplateKey(event.target.value)}>
              {templates.map((template) => (
                <option key={template.template_key} value={template.template_key}>{template.template_key}</option>
              ))}
            </select>
            <textarea rows="10" value={templateBody} onChange={(event) => setTemplateBody(event.target.value)} />
            <button type="submit">Save template</button>
          </form>
        </section>
      </main>
    </div>
  );
}

function formatForwardingState(order) {
  if (!order.forward_delivery_status) {
    return 'Not sent';
  }

  const recipient = order.forwarded_to ? ` to ${order.forwarded_to}` : '';
  return `${order.forward_delivery_status}${recipient}`;
}
