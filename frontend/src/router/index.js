import { createRouter, createWebHistory } from "vue-router";
import { useAuthStore } from "../stores/auth";

// Route Components
import Home from "../pages/shared/Home.vue";
import Signup from "../pages/auth/SignUp.vue";
import Login from "../pages/auth/Login.vue";
import CompleteProfile from "../pages/auth/CompleteProfile.vue";
import BuyerDashboard from "../pages/buyer/Dashboard.vue";
import FarmerDashboard from "../pages/farmer/Dashboard.vue";
import RiderDashboard from "../pages/rider/Dashboard.vue";
import Dashboard from "../components/dashboard/Dashboard.vue";

const routes = [
  { path: "/", name: "Home", component: Home },
  { path: "/signup", name: "Signup", component: Signup },
  { path: "/login", name: "Login", component: Login },

  // Profile Completion (Requires Auth but NOT Verification)
  {
    path: "/complete-profile",
    name: "CompleteProfile",
    component: CompleteProfile,
    meta: { requiresAuth: true },
  },

  // Admin Dashboard Route
  {
    path: "/admin",
    name: "AdminDashboard",
    component: Dashboard,
    meta: { requiresAuth: true, role: "admin" }, // Protect it for admin role
    children: [
      // This maps the GET requests from your image to specific sub-routes
      { path: "", name: "AdminOverview", component: () => import("../pages/admin/Overview.vue") },
      { path: "dispatch-riders", name: "AdminRiders", component: () => import("../pages/admin/Riders.vue") },
      { path: "orders", name: "AdminOrders", component: () => import("../pages/admin/Orders.vue") },
      { path: "disputes", name: "AdminDisputes", component: () => import("../pages/admin/Disputes.vue") },
      { path: "all_users", name: "AdminAllUsers", component: () => import("../pages/admin/Users.vue") },
      { path: "all_farmers", name: "AdminAllFarmers", component: () => import("../pages/admin/Farmers.vue") },
      { path: "all_payments", name: "AdminAllPayments", component: () => import("../pages/admin/Payments.vue") },
      { path: "all_farmer_profile", name: "AdminFarmerProfiles", component: () => import("../pages/admin/Profiles.vue") },
      { path: "all_products", name: "AdminProducts", component: () => import("../pages/admin/Products.vue") },
    ],
  },

  // Role-Specific Dashboards
  {
    path: "/buyer",
    name: "BuyerDashboard",
    component: BuyerDashboard,
    meta: { requiresAuth: true, role: "buyer" },
  },
  {
    path: "/farmer",
    name: "FarmerDashboard",
    component: FarmerDashboard,
    meta: { requiresAuth: true, role: "farmer" },
  },
  {
    path: "/rider",
    name: "RiderDashboard",
    component: RiderDashboard,
    meta: { requiresAuth: true, role: "rider" },
  },
  {
    path: "/marketplace",
    name: "Marketplace",
    component: () => import("../pages/shared/Marketplace.vue"),
  },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

// --- ROUTE GUARD LOGIC ---
router.beforeEach((to, from, next) => {
  const authStore = useAuthStore();
  const { isAuthenticated, user } = authStore;

  // 1. If the route requires Auth and user is NOT logged in, go to Login
  if (to.meta.requiresAuth && !isAuthenticated) {
    return next({ name: "Login" });
  }

  // 2. IMPORTANT FIX: If user is logged in, but we haven't fetched the user object yet
  // We should wait or redirect to login if the session is broken
  if (to.meta.requiresAuth && isAuthenticated && !user) {
    // This happens on refresh. You might need to call an 'getUser' action here
    // For now, let's just prevent the crash:
    return next({ name: "Login" });
  }

  // 3. Prevent logged-in users from seeing Login/Signup
  if (isAuthenticated && (to.name === "Login" || to.name === "Signup")) {
    if (!user) return next(); // Safety break
    const dashboardName = `${user.role.charAt(0).toUpperCase() + user.role.slice(1)}Dashboard`;
    return next({ name: dashboardName });
  }

  // 4. Role-Based Access (Added optional chaining ?. to prevent the 'role' error)
  if (to.meta.role && user?.role !== to.meta.role) {
    if (!user) return next({ name: "Login" });
    const dashboardName = `${user.role.charAt(0).toUpperCase() + user.role.slice(1)}Dashboard`;
    return next({ name: dashboardName });
  }

  // 5. Verification Check for Farmers (Added optional chaining)
  if (
    to.meta.requiresVerification &&
    user?.role === "farmer" &&
    !user?.isVerified
  ) {
    return next({ name: "CompleteProfile" });
  }

  next();
});
export default router;
