const DEFAULT_BASE_URL = 'https://biomed-production.up.railway.app';

function makeHeaders(apiKey) {
  const headers = { 'Content-Type': 'application/json' };
  if (apiKey) {
    headers['x-api-key'] = apiKey;
  }
  return headers;
}

async function request(path, options = {}, apiKey, baseUrl = DEFAULT_BASE_URL) {
  const response = await fetch(`${baseUrl}${path}`, {
    ...options,
    headers: {
      ...makeHeaders(apiKey),
      ...(options.headers || {}),
    },
  });

  if (response.status === 204) {
    return null;
  }

  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.detail || data.error || 'Request failed');
  }
  return data;
}

export const dashboardApi = {
  getOrders: (apiKey, baseUrl, status = '', forwardStatus = '') => {
    const params = new URLSearchParams();
    if (status) {
      params.set('status', status);
    }
    if (forwardStatus) {
      params.set('forward_status', forwardStatus);
    }
    const query = params.toString();
    return request(`/api/orders${query ? `?${query}` : ''}`, {}, apiKey, baseUrl);
  },
  getOrder: (id, apiKey, baseUrl) => request(`/api/orders/${id}`, {}, apiKey, baseUrl),
  getCustomers: (apiKey, baseUrl) => request('/api/customers', {}, apiKey, baseUrl),
  getTemplates: (apiKey, baseUrl) => request('/api/templates', {}, apiKey, baseUrl),
  getCustomerOrders: (phoneNumber, apiKey, baseUrl) => request(`/api/customers/${encodeURIComponent(phoneNumber)}/orders`, {}, apiKey, baseUrl),
  updateCustomerAddress: (phoneNumber, payload, apiKey, baseUrl) => request(`/api/customers/${encodeURIComponent(phoneNumber)}/address`, { method: 'PUT', body: JSON.stringify(payload) }, apiKey, baseUrl),
  getProducts: (apiKey, baseUrl) => request('/api/products', {}, apiKey, baseUrl),
  createProduct: (payload, apiKey, baseUrl) => request('/api/products', { method: 'POST', body: JSON.stringify(payload) }, apiKey, baseUrl),
  updateProduct: (id, payload, apiKey, baseUrl) => request(`/api/products/${id}`, { method: 'PUT', body: JSON.stringify(payload) }, apiKey, baseUrl),
  deleteProduct: (id, apiKey, baseUrl) => request(`/api/products/${id}`, { method: 'DELETE' }, apiKey, baseUrl),
  updateTemplate: (templateKey, body, apiKey, baseUrl) => request(`/api/templates/${encodeURIComponent(templateKey)}`, { method: 'PUT', body: JSON.stringify({ body }) }, apiKey, baseUrl),
  confirmOrder: (id, apiKey, baseUrl) => request(`/api/orders/${id}/confirm`, { method: 'POST' }, apiKey, baseUrl),
  updateOrderStatus: (id, status, apiKey, baseUrl) => request(`/api/orders/${id}/status`, { method: 'PUT', body: JSON.stringify({ status }) }, apiKey, baseUrl),
  forwardOrder: (id, apiKey, baseUrl, force = false) => request(`/api/orders/${id}/forward`, { method: 'POST', body: JSON.stringify({ force }) }, apiKey, baseUrl),
};
