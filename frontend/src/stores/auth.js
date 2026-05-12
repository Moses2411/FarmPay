import { defineStore } from "pinia";
import { ref, computed } from "vue";
import router from "../router";

export const useAuthStore = defineStore("auth", () => {
  // --- State ---
  const user = ref(JSON.parse(localStorage.getItem("farmpay_user")) || null); // Holds { id, fullName, email, role, isVerified }
  //   const user = ref(
  //     JSON.parse(localStorage.getItem("farmpay_user")) || {
  //       role: "buyer",
  //       isVerified: true,
  //     },
  //   );
  const token = ref(localStorage.getItem("farmpay_token") || null);
  const isAuthenticated = computed(() => !!token.value);
  //   const isAuthenticated = true;

  // --- Actions ---

  // Set user data after Login or Signup
  function setAuth(userData, userToken) {
    user.value = {
      id: userData.id,
      fullName: userData.full_name || userData.fullName, // Handle both cases
      email: userData.email,
      role: userData.role,
      isVerified: userData.isVerified ?? false,
      profile: userData.profile || null,
    };
    token.value = userToken;
    localStorage.setItem("farmpay_token", userToken);
    localStorage.setItem("farmpay_user", JSON.stringify(user.value));
  }

  // Update verification status (after Complete Profile)
  function setVerified(status) {
    if (user.value) {
      user.value.isVerified = status;
    }
  }

  // Clear session (Logout)
  function logout() {
    user.value = null;
    token.value = null;
    localStorage.removeItem("farmpay_token");
    localStorage.removeItem("farmpay_user");

    router.push("/login");
    // Optional: redirect to login
  }

  return {
    user,
    token,
    isAuthenticated,
    setAuth,
    setVerified,
    logout,
  };
});
