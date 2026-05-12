<script setup>
import { ref, onMounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { useForm, useField } from 'vee-validate';
import * as yup from 'yup';
import { useAuthStore } from '../../stores/auth';
import { login as loginApi, getUserProfile } from '../../api/api';
import { 
  Wallet, Mail, Lock, ArrowRight, 
  ShieldCheck, CheckCircle2, LogIn 
} from 'lucide-vue-next';

const route = useRoute();
const router = useRouter();
const auth = useAuthStore();

// Banner State
const showBanner = ref(false);
const bannerMessage = ref('');
const loginError = ref(null);

// 1. Validation Schema
const schema = yup.object({
  email: yup.string().required('Email is required').email('Enter a valid email'),
  password: yup.string().required('Password is required'),
});

const { handleSubmit, errors, isSubmitting } = useForm({
  validationSchema: schema,
});

const { value: email } = useField('email');
const { value: password } = useField('password');

// 2. Lifecycle: Check for Redirect Messages
onMounted(() => {
  if (route.query.registered === 'true') {
    showBanner.value = true;
    bannerMessage.value = route.query.message || "Account created! Please sign in.";
    // Auto-hide after 8 seconds
    setTimeout(() => (showBanner.value = false), 8000);
  }
});

// 3. Login Handler
const onLogin = handleSubmit(async (values) => {
  loginError.value = null;
  try {
    // A. Get the response from the API
    // Note: Axios responses contain the backend payload inside 'data'
    const response = await loginApi({
      email: values.email,
      password: values.password
    });
    console.log(response.access_token)
    // B. Extract Token and User Data
    // Backend usually returns: { access_token: "...", user: { role: "...", ... } }
    const token = response.access_token;
    const userData = {
      id: response.id,
      fullName: response.full_name,
      email: response.email,
      role: response.role==='dispatch_rider'? 'rider': response.role,
      isVerified: response.is_verified,
      phoneNumber: response.phone_number
    }

    console.log(userData)
    // C. Save to LocalStorage
    // Make sure your Axios Interceptor is looking for 'farmpay_token'
    localStorage.setItem('farmpay_token', token);

    // D. Update Pinia Store
    auth.setAuth(userData, token);

    // E. Role-Based Redirection
    // Note: Use string matching or lowercase to ensure consistency
    const role = userData.role?.toLowerCase();
    
    if (role === 'farmer') {
      // Check verification status from backend
      if (!userData.isVerified) {
        return router.push({ name: 'CompleteProfile' });
      }
      return router.push({ name: 'FarmerDashboard' });
    } 
    
    if (role === 'buyer') {
      return router.push({ name: 'BuyerDashboard' });
    }

    if (role === 'rider') {
      // Ensure this route is defined in your router to avoid warnings
      return router.push({ name: 'RiderDashboard' });
    }

  } catch (err) {
    // Improved error capturing for the UI
    loginError.value = err.response?.data?.detail || "Invalid email or password.";
    console.error("Login Error:", err.response?.data || err);
  }
});
</script>

<template>
  <div class="min-h-screen bg-[#061209] flex flex-col lg:flex-row font-sans text-[#f0ede4]">
    
    <div class="hidden lg:flex lg:w-5/12 bg-[#0d2010] p-12 flex-col justify-between border-r border-white/5">
      <div>
        <router-link to="/" class="flex items-center gap-3 mb-16">
          <div class="w-8 h-8 bg-[#2d7a18] rounded-full flex items-center justify-center text-white">
            <Wallet :size="16" />
          </div>
          <span class="font-serif text-xl font-semibold tracking-tight">FarmPay<span class="text-[#5cb83a]">.</span>ng</span>
        </router-link>

        <h2 class="font-serif text-5xl leading-tight mb-8">
          Welcome back to <br/>
          <span class="text-[#5cb83a] italic">the Market.</span>
        </h2>

        <div class="space-y-6">
          <div class="flex gap-4 items-start">
            <div class="mt-1 text-[#5cb83a]"><ShieldCheck :size="20" /></div>
            <div>
              <p class="font-bold">Secured Sessions</p>
              <p class="text-sm text-white/40">Your account is protected by industry-standard encryption.</p>
            </div>
          </div>
          <div class="flex gap-4 items-start">
            <div class="mt-1 text-[#5cb83a]"><CheckCircle2 :size="20" /></div>
            <div>
              <p class="font-bold">Instant Access</p>
              <p class="text-sm text-white/40">Manage your farm listings or track your orders in real-time.</p>
            </div>
          </div>
        </div>
      </div>
      <div class="text-[10px] uppercase tracking-widest text-white/20">
        © 2026 FarmPay.ng · Secure Portal
      </div>
    </div>

    <div class="flex-1 flex items-center justify-center p-6 md:p-12 relative overflow-hidden">
      
      <transition name="slide-down">
        <div v-if="showBanner" 
             class="absolute top-8 left-1/2 -translate-x-1/2 w-full max-w-sm bg-[#5cb83a]/10 border border-[#5cb83a]/30 p-4 rounded-2xl flex items-center gap-3 shadow-2xl backdrop-blur-md z-50 mx-4">
          <div class="bg-[#5cb83a] p-1 rounded-full text-white">
            <CheckCircle2 :size="16" />
          </div>
          <p class="text-xs font-bold text-[#7bc95a]">{{ bannerMessage }}</p>
        </div>
      </transition>

      <div class="w-full max-w-md space-y-8">
        <div class="text-center lg:text-left">
          <div class="w-12 h-12 bg-[#2d7a18]/20 rounded-2xl flex items-center justify-center mb-6 mx-auto lg:mx-0">
            <LogIn class="text-[#5cb83a]" :size="24" />
          </div>
          <h1 class="text-3xl font-serif mb-2">Sign In</h1>
          <p class="text-white/40 text-sm">Enter your credentials to access your FarmPay account.</p>
        </div>

        <div v-if="loginError" class="p-4 bg-red-500/10 border border-red-500/20 rounded-xl text-red-400 text-xs font-medium">
          {{ loginError }}
        </div>

        <form @submit="onLogin" class="space-y-5">
          <div class="space-y-1">
            <label class="text-[10px] uppercase font-bold text-white/30 ml-1 tracking-widest">Email Address</label>
            <div class="relative">
              <Mail class="absolute left-4 top-1/2 -translate-y-1/2 text-white/20" :size="18" />
              <input v-model="email" type="email" placeholder="amina@farmpay.ng" 
                :class="errors.email ? 'border-red-500/50' : 'border-white/10'"
                class="w-full bg-white/5 border rounded-xl py-4 pl-12 pr-4 focus:outline-none focus:border-[#5cb83a] transition-colors">
            </div>
            <span class="text-red-400 text-[10px] ml-1">{{ errors.email }}</span>
          </div>

          <div class="space-y-1">
            <div class="flex justify-between items-center px-1">
              <label class="text-[10px] uppercase font-bold text-white/30 tracking-widest">Password</label>
              <router-link to="/forgot-password" class="text-[10px] text-[#5cb83a] hover:underline font-bold uppercase tracking-widest">Forgot?</router-link>
            </div>
            <div class="relative">
              <Lock class="absolute left-4 top-1/2 -translate-y-1/2 text-white/20" :size="18" />
              <input v-model="password" type="password" placeholder="••••••••"
                :class="errors.password ? 'border-red-500/50' : 'border-white/10'"
                class="w-full bg-white/5 border rounded-xl py-4 pl-12 pr-4 focus:outline-none focus:border-[#5cb83a] transition-colors">
            </div>
            <span class="text-red-400 text-[10px] ml-1">{{ errors.password }}</span>
          </div>

          <button type="submit" :disabled="isSubmitting"
            class="w-full bg-[#2d7a18] hover:bg-[#3a9e20] text-white py-4 rounded-xl font-bold flex items-center justify-center gap-2 transition-all disabled:opacity-50 mt-4 shadow-lg shadow-[#2d7a18]/10">
            <span v-if="!isSubmitting">Sign In to Dashboard</span>
            <span v-else class="animate-pulse tracking-widest text-xs uppercase">Authenticating...</span>
            <ArrowRight v-if="!isSubmitting" :size="18" />
          </button>
        </form>

        <p class="text-center text-sm text-white/40">
          New to the platform? 
          <router-link to="/signup" class="text-[#5cb83a] font-bold hover:underline">Create Account</router-link>
        </p>
      </div>
    </div>
  </div>
</template>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display&family=DM+Sans:wght@400;500;700&display=swap');
.font-serif { font-family: 'DM Serif Display', serif; }
.font-sans { font-family: 'DM Sans', sans-serif; }

/* Animation for the banner */
.slide-down-enter-active, .slide-down-leave-active {
  transition: all 0.5s cubic-bezier(0.16, 1, 0.3, 1);
}
.slide-down-enter-from, .slide-down-leave-to {
  opacity: 0;
  transform: translate(-50%, -40px);
}
</style>