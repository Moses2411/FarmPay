import axios from "axios";

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL,
  headers: {
    Accept: "application/json",
  },
});

api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem("farmpay_token");
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error),
);

api.interceptors.response.use(
  (response) => response.data,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem("farmpay_token");
      localStorage.removeItem("farmpay_user");
      window.location.href = "/login";
    }
    return Promise.reject(error.response?.data || error.message);
  },
);

export const login = (data) => api.post("/auth/login", data);
export const register = (data) => api.post("/auth/register", data);

export const completeProfile = (data) => api.post("/auth/farmer_profile", data);
export const getUserProfile = () => api.get("/auth/profile");
export const getMyProducts = () => api.get('/products/my-products');
export const deleteProduct = (id) => api.delete(`/products/${id}`);
export const getProductReviews = (productId) => api.get(`/reviews/product/${productId}`);
export const createReview = (data) => api.post("/reviews/", data);

export const createRider = (data) => api.post("/admin/create-dispatch-rider", data);
export const getAllRiders = (data) => api.get(`/admin/dispatch-riders/details?page=${data.page}&per_page=${data.per_page}`);
export const assignRider = (data) => api.put(`/admin/assign-rider/${data.order_id}/${data.rider_id}?rider_status=busy`);

export const getAllOrders = (data) => api.get(`/admin/orders/details?page=${data.page}&per_page=${data.per_page}`);

export const getAllUsers = (data) => api.get(`/admin/users/details?page=${data.page}&per_page=${data.per_page}`);
export const verifyUser = (userId) => api.put(`/admin/verify_user/${userId}`);
export const getAllPayment = (data) => api.get(`/admin/payments/details?page=${data.page}&per_page=${data.per_page}`);

export const getFarmersProfile = (data) => api.get(`/admin/farmer-profiles/details?page=${data.page}&per_page=${data.per_page}`);

export const getAllProducts = (data) => api.get(`/admin/products/details?page=${data.page}&per_page=${data.per_page}`);
export const getAdminDashboardCounts = () => api.get('/admin/dashboard/counts');

export const getAllDisputes = (data) => api.get(`/admin/disputes?page=${data.page}&per_page=${data.per_page}`);
export const resolveDispute = (data) => api.put(`/admin/dispute/${data.disputeId}/resolve`, data.body);

export const getRiderOrders = () => api.get('/rider/rider/orders');
export const markOrderPickedUp = (orderId) => api.patch(`/rider/order/${orderId}/picked-up');
export const confirmDelivery = (orderId, otp) => api.post(`/rider/confirm-delivery/${orderId}?otp=${otp}`);
export const toggleRiderStatus = (isAvailable) => api.post('/rider/status', { is_available: isAvailable });

export const getFarmerPayouts = () => api.get('/auth/payouts');

export default api;