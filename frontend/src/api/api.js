import axios from "axios";
const api = axios.create({
  // Use environment variables for flexibility
  baseURL: "https://farmpay-j8a4.onrender.com/",
  // Remove the hardcoded Content-Type header to allow flexibility for uploads
  headers: {
    Accept: "application/json",
  },
});

// Request interceptor: Attach the token from the store/localStorage
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

// Response interceptor: Global error handling
api.interceptors.response.use(
  (response) => response.data, // This returns the raw response body (the string for login)
  (error) => {
    // Handle 401 Unauthorized (e.g., token expired)
    if (error.response?.status === 401) {
      localStorage.removeItem("farmpay_token");
      localStorage.removeItem("farmpay_user");
      window.location.href = "/login"; // Force logout
    }
    return Promise.reject(error.response?.data || error.message);
  },
);

// Auth APIs
export const login = (data) => api.post("/auth/login", data);
export const register = (data) => api.post("/auth/register", data);

// Farmer Specific
export const completeProfile = (data) => api.post("/auth/farmer_profile", data);
export const getUserProfile = () => api.get("/auth/me"); // Assuming this exists

export const createRider = (data) => api.post("/admin/create-dispatch-rider", data)
export const getAllRiders = (data) => api.get(`/admin/dispatch-riders/details?page=${data.page}&per_page=${data.per_page}`);
export const assignRider = (data) => api.put(`/admin/assign-rider/${data.order_id}/${data.rider_id}`);

// all orders
export const getAllOrders = (data) => api.get(`/admin/orders/details?page=${data.page}&per_page=${data.per_page}`);

// all users
export const getAllUsers = (data) => api.get(`/admin/users/details?page=${data.page}&per_page=${data.per_page}`);
// all payment
export const getAllPayment = (data) => api.get(`/admin/payments/details?page=${data.page}&per_page=${data.per_page}`);

// farmers profile
export const getFarmersProfile = (data) => api.get(`/admin/farmer-profiles/details?page=${data.page}&per_page=${data.per_page}`);

// all products
export const getAllProducts = (data) => api.get(`/admin/products/details?page=${data.page}&per_page=${data.per_page}`);

// resolve dispute
export const getAllDisputes = (data) => api.get(`/admin/disputes?page=${data.page}&per_page=${data.per_page}`);
export const resolveDispute = (data) => api.put(`/admin/dispute/${data.disputeId}/resolve`, data.body);
// Rest of your APIs...
export default api;
