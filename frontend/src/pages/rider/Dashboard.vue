<script setup>
import { ref, onMounted } from 'vue';
import api from '@/api/api';
import { 
  Package, 
  ShieldCheck, 
  Loader2, 
  MapPin, 
  Navigation,
  CheckCircle,
  Inbox
} from 'lucide-vue-next';

// 1. Reactive State
const activeOrders = ref([]);
const isLoading = ref(true);
const isOtpModalOpen = ref(false);
const selectedOrder = ref(null);
const otpValue = ref('');
const isVerifying = ref(false);

// 2. Fetch Tasks from Backend
const fetchRiderTasks = async () => {
  isLoading.value = true;
  try {
    // Assuming your backend route for rider assignments
    const response = await api.get('/rider/rider/orders'); 
    activeOrders.value = response;
  } catch (err) {
    console.error("Failed to load rider tasks:", err);
  } finally {
    isLoading.value = false;
  }
};

onMounted(fetchRiderTasks);

// 3. OTP Modal Logic
const openOtpModal = (order) => {
  selectedOrder.value = order;
  otpValue.value = ''; 
  isOtpModalOpen.value = true;
};

// 4. Verification Logic
const handleVerifyOtp = async () => {
  if (otpValue.value.length < 6) return;

  isVerifying.value = true;
  try {
    // Correctly structured endpoint based on your previous controller logic
    await api.post(`/rider/confirm-delivery/${selectedOrder.value.id}`, {
      otp_code: otpValue.value
    });

    // Success: Remove from list and close modal
    activeOrders.value = activeOrders.value.filter(o => o.id !== selectedOrder.value.id);
    isOtpModalOpen.value = false;
    alert("Delivery Confirmed! Funds released to Farmer.");
  } catch (err) {
    const errorMsg = err.response?.message || "Invalid OTP code.";
    alert(errorMsg);
  } finally {
    isVerifying.value = false;
  }
};
</script>

<template>
  <div class="min-h-screen bg-[#061209] text-[#f0ede4] p-6 pb-24 font-sans">
    <header class="flex justify-between items-center mb-8">
      <div>
        <h1 class="text-2xl font-serif">Rider Terminal</h1>
        <p class="text-[#5cb83a] text-sm flex items-center gap-2">
          <span class="w-2 h-2 bg-[#5cb83a] rounded-full animate-pulse"></span>
          Duty Status: Active
        </p>
      </div>
      <div class="bg-white/5 px-4 py-2 rounded-2xl border border-white/10 text-center">
        <span class="text-[10px] uppercase tracking-widest block opacity-40">Active Tasks</span>
        <span class="text-xl font-bold text-[#5cb83a]">{{ activeOrders.length }}</span>
      </div>
    </header>

    <section class="space-y-6">
      <div class="flex items-center justify-between px-2">
        <h3 class="text-xs uppercase tracking-[0.2em] font-bold text-white/30">Current Queue</h3>
        <button @click="fetchRiderTasks" class="text-[10px] text-[#5cb83a] uppercase font-bold">Refresh</button>
      </div>

      <div v-if="isLoading" class="flex flex-col items-center justify-center py-20">
        <Loader2 class="animate-spin text-[#5cb83a] mb-4" :size="32" />
        <p class="text-[10px] uppercase tracking-widest opacity-40">Syncing with Hub...</p>
      </div>

      <div v-else-if="activeOrders.length === 0" class="text-center py-20 bg-white/2 rounded-[2.5rem] border border-dashed border-white/10">
        <Inbox class="mx-auto mb-4 text-white/10" :size="48" />
        <p class="text-white/40 italic">No pending deliveries assigned.</p>
      </div>

      <div v-else v-for="order in activeOrders" :key="order.id" 
           class="bg-[#0d2010] border border-white/10 p-6 rounded-[2.5rem] relative overflow-hidden group">
        <div class="relative z-10">
          <div class="flex items-start justify-between mb-6">
            <div class="bg-[#5cb83a]/10 p-3 rounded-2xl">
              <Package class="text-[#5cb83a]" :size="24" />
            </div>
            <div class="text-right">
              <span class="text-[10px] uppercase text-white/40 block">Order ID</span>
              <span class="font-mono text-sm">#{{ order.id.slice(-8).toUpperCase() }}</span>
            </div>
          </div>

          <div class="space-y-4 mb-8">
            <div class="flex gap-4">
              <div class="flex flex-col items-center gap-1 mt-1">
                <div class="w-2 h-2 rounded-full bg-[#5cb83a]"></div>
                <div class="w-0.5 h-10 border-l border-dashed border-white/20"></div>
                <div class="w-2 h-2 rounded-full border border-[#5cb83a]"></div>
              </div>
              <div class="space-y-4">
                <div>
                  <p class="text-[10px] uppercase text-white/30 leading-none mb-1">Pickup From</p>
                  <p class="text-sm font-medium">{{ order.pickup_address || order.pickup_location }}</p>
                </div>
                <div>
                  <p class="text-[10px] uppercase text-white/30 leading-none mb-1">Deliver To</p>
                  <p class="text-sm font-medium">{{ order.delivery_address || order.dropoff_location }}</p>
                </div>
              </div>
            </div>
          </div>

          <button @click="openOtpModal(order)" 
                  class="w-full bg-[#5cb83a] text-[#061209] py-4 rounded-2xl font-bold flex items-center justify-center gap-2 hover:bg-[#4ea131] transition-colors">
            <ShieldCheck :size="18" />
            Confirm Delivery (OTP)
          </button>
        </div>
      </div>
    </section>

    <div v-if="isOtpModalOpen" class="fixed inset-0 z-50 flex items-center justify-center p-6 bg-[#061209]/95 backdrop-blur-md">
      <div class="bg-[#0d2010] border border-white/10 w-full max-w-sm rounded-[2.5rem] p-8 shadow-2xl">
        <div class="text-center mb-6">
          <div class="w-16 h-16 bg-[#5cb83a]/10 rounded-full flex items-center justify-center mx-auto mb-4">
            <ShieldCheck class="text-[#5cb83a]" :size="32" />
          </div>
          <h2 class="text-xl font-serif text-[#f0ede4]">Confirm Delivery</h2>
          <p class="text-white/40 text-xs mt-2">Enter the code from the buyer's screen.</p>
        </div>

        <div class="space-y-6">
          <input 
            v-model="otpValue"
            type="text" 
            maxlength="6"
            placeholder="······"
            class="w-full bg-white/5 border border-white/10 rounded-2xl py-5 px-4 text-center text-3xl font-mono tracking-[0.2em] outline-none focus:border-[#5cb83a] transition-all"
          />

          <div class="flex gap-3">
            <button @click="isOtpModalOpen = false" class="flex-1 bg-white/5 hover:bg-white/10 py-4 rounded-xl font-bold">Cancel</button>
            <button 
              @click="handleVerifyOtp"
              :disabled="isVerifying || otpValue.length < 6"
              class="flex-[2] bg-[#5cb83a] disabled:opacity-30 text-[#061209] py-4 rounded-xl font-bold flex items-center justify-center gap-2"
            >
              <Loader2 v-if="isVerifying" class="animate-spin" :size="20" />
              {{ isVerifying ? 'Verifying...' : 'Verify' }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>