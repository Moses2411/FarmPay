<script setup>
import { ref, onMounted, computed } from 'vue';
import api from '@/api/api';
import { 
  Package, ShieldCheck, Loader2, 
  CheckCircle, Inbox, Truck, Clock, 
  AlertTriangle, RefreshCw, FileCheck, MapPin
} from 'lucide-vue-next';

// State
const orders = ref([]);
const isLoading = ref(true);
const activeTab = ref('pending'); 
const isOtpModalOpen = ref(false);
const selectedOrder = ref(null);
const otpValue = ref('');
const isVerifying = ref(false);

const fetchRiderTasks = async () => {
  isLoading.value = true;
  try {
    const response = await api.get('/rider/rider/orders'); 
    orders.value = response.data || response;
  } catch (err) {
    console.error("Fetch error:", err);
  } finally {
    isLoading.value = false;
  }
};

onMounted(fetchRiderTasks);

// Strict Filtering Logic
const filteredOrders = computed(() => {
  return orders.value.filter(order => {
    const dStatus = order.delivery_status;
    if (activeTab.value === 'pending') return dStatus === 'pending';
    if (activeTab.value === 'picked-up') return dStatus === 'picked-up' || dStatus === 'transit';
    if (activeTab.value === 'disputed') return dStatus === 'disputed';
    if (activeTab.value === 'delivered') return dStatus === 'delivered';
    if (activeTab.value === 'completed') return order.status === 'completed' && dStatus !== 'disputed';
    return false;
  });
});

const openOtpModal = (order) => {
  selectedOrder.value = order;
  otpValue.value = '';
  isOtpModalOpen.value = true;
};

const handleVerifyOtp = async () => {
  if (otpValue.value.length < 6) return;
  isVerifying.value = true;
  try {
    await api.post(`/rider/confirm-delivery/${selectedOrder.value.id}`, {
      otp_code: otpValue.value
    });
    await fetchRiderTasks(); // Refresh state
    isOtpModalOpen.value = false;
    activeTab.value = 'completed'; 
  } catch (err) {
    alert("Invalid OTP code.");
  } finally {
    isVerifying.value = false;
  }
};
</script>

<template>
  <div class="min-h-screen bg-[#061209] text-[#f0ede4] p-6 pb-24 font-sans">
    
    <header class="flex justify-between items-center mb-8">
      <h1 class="text-2xl font-serif tracking-tight">Rider Terminal</h1>
      <button @click="fetchRiderTasks" class="p-3 bg-white/5 rounded-2xl border border-white/10">
        <RefreshCw :size="18" :class="{ 'animate-spin': isLoading }" />
      </button>
    </header>

    <nav class="flex p-1 bg-black/40 rounded-2xl border border-white/5 mb-8 overflow-x-auto no-scrollbar gap-1">
      <button 
        v-for="tab in ['pending', 'picked-up', 'delivered', 'completed', 'disputed']" 
        :key="tab"
        @click="activeTab = tab"
        class="flex-1 min-w-22.5 py-3 text-[9px] uppercase font-bold tracking-widest rounded-xl transition-all"
        :class="activeTab === tab ? 'bg-[#5cb83a] text-[#061209]' : 'text-white/30'"
      >
        {{ tab }}
      </button>
    </nav>

    <section class="space-y-4">
      <div v-if="isLoading" class="flex justify-center py-20">
        <Loader2 class="animate-spin text-[#5cb83a]" :size="32" />
      </div>

      <div v-else-if="filteredOrders.length === 0" class="text-center py-20 bg-white/2 rounded-4xl border border-dashed border-white/10">
        <Inbox class="mx-auto mb-2 text-white/5" :size="32" />
        <p class="text-[10px] uppercase tracking-widest text-white/20">No tasks in {{ activeTab }}</p>
      </div>

      <div v-for="order in filteredOrders" :key="order.id" 
           class="bg-[#0d2010] border border-white/10 p-6 rounded-4xl">
        
        <div class="flex justify-between items-start mb-6">
          <div class="p-3 bg-white/5 rounded-2xl text-white/40">
            <Package v-if="activeTab !== 'completed'" :size="20" />
            <FileCheck v-else class="text-[#5cb83a]" :size="20" />
          </div>
          <span class="text-[10px] font-mono text-white/30 uppercase">ID: {{ order.id.slice(-8).toUpperCase() }}</span>
        </div>

        <div class="space-y-3 mb-6 border-l-2 border-[#5cb83a]/20 pl-4">
          <div>
            <span class="text-[8px] uppercase text-white/20 block mb-1">Destination</span>
            <p class="text-sm font-medium">{{ order.delivery_location }}</p>
          </div>
          <div>
            <span class="text-[8px] uppercase text-white/20 block mb-1">Total Order Value</span>
            <p class="text-lg font-serif text-[#5cb83a]">₦{{ (order.total_amount || 0).toLocaleString() }}</p>
          </div>
        </div>

        <div v-if="activeTab === 'pending'">
          <button class="w-full bg-white text-black py-4 rounded-xl font-bold text-[10px] uppercase tracking-widest active:scale-95 transition-all">
            Confirm Pickup
          </button>
        </div>

        <div v-if="activeTab === 'picked-up'">
          <button @click="openOtpModal(order)" class="w-full bg-[#5cb83a] text-black py-4 rounded-xl font-bold text-[10px] uppercase tracking-widest shadow-lg shadow-[#5cb83a]/10 active:scale-95 transition-all">
            Enter Delivery OTP
          </button>
        </div>

        <div v-if="activeTab === 'disputed'" class="text-center p-3 bg-red-500/10 rounded-xl border border-red-500/20">
          <p class="text-[9px] text-red-500 font-bold uppercase">Order Flagged: Disputed</p>
        </div>

        <div v-if="activeTab === 'completed'" class="flex justify-between items-center text-[#5cb83a]">
          <span class="text-[10px] font-bold uppercase">Settled</span>
          <CheckCircle :size="16" />
        </div>

      </div>
    </section>

    <div v-if="isOtpModalOpen" class="fixed inset-0 z-50 flex items-center justify-center p-6 bg-[#061209]/95 backdrop-blur-md">
      <div class="bg-[#0d2010] border border-white/10 w-full max-w-sm rounded-[2.5rem] p-8 shadow-2xl">
        <div class="text-center mb-6">
          <ShieldCheck class="text-[#5cb83a] mx-auto mb-4" :size="40" />
          <h2 class="text-xl font-serif">Confirm OTP</h2>
          <p class="text-white/40 text-xs mt-2">Enter code from buyer to release funds</p>
        </div>

        <input v-model="otpValue" type="text" maxlength="6" placeholder="······"
               class="w-full bg-white/5 border border-white/10 rounded-2xl py-4 text-center text-3xl font-mono tracking-widest outline-none focus:border-[#5cb83a] transition-all mb-6" />

        <div class="flex gap-3">
          <button @click="isOtpModalOpen = false" class="flex-1 bg-white/5 py-4 rounded-xl text-xs font-bold">Cancel</button>
          <button @click="handleVerifyOtp" :disabled="isVerifying || otpValue.length < 6"
                  class="flex-2 bg-[#5cb83a] text-[#061209] py-4 rounded-xl text-xs font-bold flex items-center justify-center gap-2">
            <Loader2 v-if="isVerifying" class="animate-spin" :size="16" />
            Verify Delivery
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.no-scrollbar::-webkit-scrollbar { display: none; }
.no-scrollbar { -ms-overflow-style: none; scrollbar-width: none; }
</style>