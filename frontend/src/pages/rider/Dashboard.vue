<script setup>
import { ref, onMounted, computed } from 'vue';
import { useRouter } from 'vue-router';
import { useAuthStore } from '../../stores/auth';
import { 
  getRiderOrders, 
  markOrderPickedUp, 
  confirmDelivery, 
  toggleRiderStatus 
} from '@/api/api';
import { 
  Package, ShieldCheck, Loader2, 
  CheckCircle, Inbox, RefreshCw, 
  FileCheck, MapPin, LogOut, Truck,
  User, Phone, ChevronRight, XCircle,
  CircleDot, Clock, AlertTriangle, Check
} from 'lucide-vue-next';

const router = useRouter();

// --- State Management ---
const orders = ref([]);
const isLoading = ref(true);
const activeTab = ref('pending'); 
const isOtpModalOpen = ref(false);
const selectedOrder = ref(null);
const otpValue = ref('');
const isVerifying = ref(false);
const isPickingUp = ref(false);
const isTogglingAvailability = ref(false);
const riderAvailability = ref(true);
const errorMessage = ref('');
const successMessage = ref('');

// --- Auth Actions ---
const auth = useAuthStore();

// --- API Actions ---
const fetchRiderTasks = async () => {
  isLoading.value = true;
  errorMessage.value = '';
  try {
    orders.value = await getRiderOrders();
  } catch (err) {
    console.error("Fetch error:", err);
    errorMessage.value = err.detail || "Failed to load orders";
  } finally {
    isLoading.value = false;
  }
};

const toggleAvailability = async () => {
  isTogglingAvailability.value = true;
  try {
    const newStatus = !riderAvailability.value;
    await toggleRiderStatus(newStatus);
    riderAvailability.value = newStatus;
    showSuccess(newStatus ? 'You are now online and available for deliveries' : 'You are now offline');
  } catch (err) {
    console.error("Status toggle error:", err);
    showError(err.detail || "Failed to update availability");
  } finally {
    isTogglingAvailability.value = false;
  }
};

const confirmPickup = async (order) => {
  isPickingUp.value = true;
  errorMessage.value = '';
  try {
    await markOrderPickedUp(order.id);
    showSuccess('Order marked as picked up! In transit to delivery location.');
    await fetchRiderTasks();
    activeTab.value = 'in-transit';
  } catch (err) {
    console.error("Pickup error:", err);
    showError(err.detail || "Failed to confirm pickup");
  } finally {
    isPickingUp.value = false;
  }
};

const openOtpModal = (order) => {
  selectedOrder.value = order;
  otpValue.value = '';
  errorMessage.value = '';
  isOtpModalOpen.value = true;
};

const handleVerifyOtp = async () => {
  if (otpValue.value.length < 6) return;
  isVerifying.value = true;
  errorMessage.value = '';
  try {
    await confirmDelivery(selectedOrder.value.id, otpValue.value);
    showSuccess('Delivery confirmed! Payment has been released to farmer.');
    await fetchRiderTasks(); 
    isOtpModalOpen.value = false;
    activeTab.value = 'completed'; 
  } catch (err) {
    console.error("OTP verification error:", err);
    errorMessage.value = err.detail || "Invalid OTP code. Please check and try again.";
  } finally {
    isVerifying.value = false;
  }
};

const showError = (msg) => {
  errorMessage.value = msg;
  setTimeout(() => errorMessage.value = '', 5000);
};

const showSuccess = (msg) => {
  successMessage.value = msg;
  setTimeout(() => successMessage.value = '', 5000);
};

onMounted(fetchRiderTasks);

// --- Filtering Logic ---
const tabConfig = [
  { key: 'pending', label: 'Pending', status: 'pending' },
  { key: 'in-transit', label: 'In Transit', status: ['assigned', 'in_transit'] },
  { key: 'completed', label: 'Completed', status: 'completed' },
  { key: 'disputed', label: 'Disputed', status: 'disputed' },
];

const filteredOrders = computed(() => {
  return orders.value.filter(order => {
    const dStatus = order.delivery_status?.toLowerCase();
    const oStatus = order.status?.toLowerCase();
    
    if (activeTab.value === 'pending') {
      return dStatus === 'pending' || dStatus === 'assigned';
    }
    if (activeTab.value === 'in-transit') {
      return dStatus === 'in_transit';
    }
    if (activeTab.value === 'completed') {
      return oStatus === 'completed' && dStatus !== 'disputed';
    }
    if (activeTab.value === 'disputed') {
      return dStatus === 'disputed';
    }
    return false;
  });
});

// --- Stats ---
const stats = computed(() => ({
  pending: orders.value.filter(o => o.delivery_status === 'pending' || o.delivery_status === 'assigned').length,
  inTransit: orders.value.filter(o => o.delivery_status === 'in_transit').length,
  completed: orders.value.filter(o => o.status === 'completed' && o.delivery_status !== 'disputed').length,
  disputed: orders.value.filter(o => o.delivery_status === 'disputed').length,
}));

// Format order items for display
const getOrderItemsSummary = (order) => {
  if (order.order_items && order.order_items.length > 0) {
    return order.order_items.map(item => item.product?.name || 'Produce').join(', ');
  }
  return 'Produce Order';
};

const getBuyerInfo = (order) => {
  if (order.buyer) {
    return {
      name: order.buyer.full_name || 'Buyer',
      phone: order.buyer.phone_number || 'N/A'
    };
  }
  return { name: 'Buyer', phone: 'N/A' };
};
</script>

<template>
  <div class="min-h-screen bg-[#061209] text-[#f0ede4] font-sans">
    <!-- Toast Messages -->
    <div v-if="errorMessage" class="fixed top-4 left-1/2 -translate-x-1/2 z-50 bg-red-500/90 text-white px-6 py-3 rounded-2xl shadow-2xl flex items-center gap-3 animate-slide-down">
      <AlertTriangle :size="18" />
      <span class="text-sm font-bold">{{ errorMessage }}</span>
    </div>

    <div v-if="successMessage" class="fixed top-4 left-1/2 -translate-x-1/2 z-50 bg-[#5cb83a]/90 text-[#061209] px-6 py-3 rounded-2xl shadow-2xl flex items-center gap-3 animate-slide-down">
      <Check :size="18" />
      <span class="text-sm font-bold">{{ successMessage }}</span>
    </div>

    <!-- Header -->
    <header class="p-6 pb-4">
      <div class="flex justify-between items-start mb-6">
        <div>
          <h1 class="text-2xl font-serif tracking-tight">Rider Terminal</h1>
          <div class="flex items-center gap-2 mt-2">
            <span 
              class="w-2 h-2 rounded-full animate-pulse"
              :class="riderAvailability ? 'bg-[#5cb83a]' : 'bg-amber-500'"
            ></span>
            <span class="text-[10px] uppercase tracking-[0.2em] font-bold" :class="riderAvailability ? 'text-[#5cb83a]' : 'text-amber-500'">
              {{ riderAvailability ? 'Online & Available' : 'Offline' }}
            </span>
          </div>
        </div>

        <div class="flex items-center gap-2">
          <button 
            @click="toggleAvailability" 
            :disabled="isTogglingAvailability"
            class="px-4 py-2 rounded-xl text-[10px] font-bold uppercase tracking-widest flex items-center gap-2 transition-all"
            :class="riderAvailability 
              ? 'bg-amber-500/10 text-amber-500 border border-amber-500/20 hover:bg-amber-500/20' 
              : 'bg-[#5cb83a]/10 text-[#5cb83a] border border-[#5cb83a]/20 hover:bg-[#5cb83a]/20'"
          >
            <Loader2 v-if="isTogglingAvailability" class="animate-spin" :size="14" />
            <CircleDot v-else :size="14" />
            {{ riderAvailability ? 'Go Offline' : 'Go Online' }}
          </button>
          <button @click="fetchRiderTasks" :disabled="isLoading" class="p-3 bg-white/5 rounded-2xl border border-white/10 hover:border-white/20 active:scale-90 transition-all">
            <RefreshCw :size="18" :class="{ 'animate-spin': isLoading }" />
          </button>
          <button @click="auth.logout" class="p-3 bg-red-500/5 rounded-2xl border border-red-500/10 text-red-400 hover:bg-red-500/10 active:scale-90 transition-all">
            <LogOut :size="18" />
          </button>
        </div>
      </div>

      <!-- Stats Cards -->
      <div class="grid grid-cols-4 gap-3">
        <div 
          v-for="(count, key) in stats" 
          :key="key"
          @click="activeTab = key === 'in-transit' ? 'in-transit' : key"
          class="p-4 rounded-2xl border cursor-pointer transition-all"
          :class="activeTab === key || (key === 'in-transit' && activeTab === 'in-transit') 
            ? 'bg-[#5cb83a]/10 border-[#5cb83a]/30' 
            : 'bg-white/5 border-white/10 hover:border-white/20'"
        >
          <p class="text-2xl font-serif" :class="activeTab === key ? 'text-[#5cb83a]' : ''">{{ count }}</p>
          <p class="text-[8px] uppercase tracking-widest text-white/40 font-bold mt-1">{{ key.replace('-', ' ') }}</p>
        </div>
      </div>
    </header>

    <!-- Tabs -->
    <div class="px-6 pb-6">
      <nav class="flex p-1 bg-black/40 rounded-2xl border border-white/5 overflow-x-auto no-scrollbar gap-1">
        <button 
          v-for="tab in tabConfig" 
          :key="tab.key"
          @click="activeTab = tab.key"
          class="flex-1 min-w-[100px] py-3 text-[9px] uppercase font-bold tracking-widest rounded-xl transition-all whitespace-nowrap"
          :class="activeTab === tab.key ? 'bg-[#5cb83a] text-[#061209]' : 'text-white/30 hover:text-white/60'"
        >
          {{ tab.label }}
        </button>
      </nav>
    </div>

    <!-- Orders List -->
    <div class="px-6 pb-24">
      <div v-if="isLoading" class="flex flex-col items-center justify-center py-20">
        <Loader2 class="animate-spin text-[#5cb83a] mb-4" :size="40" />
        <p class="text-white/40 text-sm">Loading your deliveries...</p>
      </div>

      <div v-else-if="filteredOrders.length === 0" class="text-center py-16 bg-white/2 rounded-[2.5rem] border border-dashed border-white/10">
        <Truck class="mx-auto mb-4 text-white/10" :size="48" />
        <p class="text-white/30 font-bold text-sm uppercase tracking-widest mb-2">No deliveries here</p>
        <p class="text-white/20 text-xs">You're all caught up!</p>
      </div>

      <div v-else class="space-y-4">
        <div 
          v-for="order in filteredOrders" 
          :key="order.id" 
          class="bg-[#0d2010] border border-white/10 p-5 rounded-[2rem] transition-all hover:border-[#5cb83a]/30"
        >
          <!-- Order Header -->
          <div class="flex justify-between items-start mb-5">
            <div class="flex items-center gap-3">
              <div class="p-2.5 bg-white/5 rounded-xl">
                <Package class="text-[#5cb83a]" :size="20" />
              </div>
              <div>
                <p class="text-xs font-bold text-white/60">Order ID</p>
                <p class="text-[10px] font-mono text-white/30">#{{ order.id.slice(-8).toUpperCase() }}</p>
              </div>
            </div>
            <div class="text-right">
              <span 
                class="px-2.5 py-1 rounded-lg text-[8px] font-bold uppercase tracking-wider"
                :class="{
                  'bg-amber-500/10 text-amber-500': order.delivery_status === 'pending' || order.delivery_status === 'assigned',
                  'bg-blue-500/10 text-blue-400': order.delivery_status === 'in_transit',
                  'bg-[#5cb83a]/10 text-[#5cb83a]': order.status === 'completed',
                  'bg-red-500/10 text-red-400': order.delivery_status === 'disputed',
                }"
              >
                {{ order.delivery_status === 'in_transit' ? 'In Transit' : order.delivery_status }}
              </span>
            </div>
          </div>

          <!-- Order Details Grid -->
          <div class="grid grid-cols-2 gap-4 mb-5">
            <div class="bg-black/20 rounded-xl p-3">
              <p class="text-[8px] uppercase text-white/30 font-bold tracking-wider mb-1">Pickup From</p>
              <p class="text-xs font-medium text-white/80">{{ order.farmer?.location || 'Farm Location' }}</p>
            </div>
            <div class="bg-black/20 rounded-xl p-3">
              <p class="text-[8px] uppercase text-white/30 font-bold tracking-wider mb-1">Deliver To</p>
              <p class="text-xs font-medium text-white/80">{{ order.delivery_location || 'Delivery Address' }}</p>
            </div>
          </div>

          <!-- Buyer Info -->
          <div class="flex items-center gap-4 mb-5 pb-4 border-b border-white/5">
            <div class="flex items-center gap-2">
              <User class="text-white/30" :size="14" />
              <span class="text-[10px] text-white/50">{{ getBuyerInfo(order).name }}</span>
            </div>
            <div class="flex items-center gap-2">
              <Phone class="text-white/30" :size="14" />
              <span class="text-[10px] text-white/50">{{ getBuyerInfo(order).phone }}</span>
            </div>
          </div>

          <!-- Footer with Amount and Actions -->
          <div class="flex justify-between items-center">
            <div>
              <p class="text-[8px] uppercase text-white/30 font-bold tracking-wider">Total Amount</p>
              <p class="text-xl font-serif text-[#5cb83a]">₦{{ (order.total_amount || 0).toLocaleString() }}</p>
            </div>

            <!-- Action Buttons based on status -->
            <div v-if="order.delivery_status === 'pending' || order.delivery_status === 'assigned'">
              <button 
                @click="confirmPickup(order)" 
                :disabled="isPickingUp"
                class="bg-white text-[#061209] px-6 py-3 rounded-xl font-bold text-[10px] uppercase tracking-widest flex items-center gap-2 hover:bg-white/90 transition-all active:scale-95 disabled:opacity-50"
              >
                <Loader2 v-if="isPickingUp" class="animate-spin" :size="14" />
                <Truck v-else :size="14" />
                Confirm Pickup
              </button>
            </div>

            <div v-else-if="order.delivery_status === 'in_transit'">
              <button 
                @click="openOtpModal(order)"
                class="bg-[#5cb83a] text-[#061209] px-6 py-3 rounded-xl font-bold text-[10px] uppercase tracking-widest flex items-center gap-2 shadow-lg shadow-[#5cb83a]/20 hover:bg-[#4da330] transition-all active:scale-95"
              >
                <ShieldCheck :size="14" />
                Verify & Complete
              </button>
            </div>

            <div v-else-if="order.delivery_status === 'disputed'" class="text-center">
              <p class="text-[9px] text-red-400 font-bold uppercase">Under Review</p>
              <p class="text-[8px] text-white/30 mt-1">Contact dispatch</p>
            </div>

            <div v-else-if="order.status === 'completed'" class="flex items-center gap-2 text-[#5cb83a]">
              <CheckCircle :size="20" />
              <span class="text-[10px] font-bold uppercase">Delivered</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- OTP Verification Modal -->
    <div v-if="isOtpModalOpen" class="fixed inset-0 z-50 flex items-center justify-center p-6 bg-[#061209]/95 backdrop-blur-md">
      <div class="bg-[#0d2010] border border-white/10 w-full max-w-sm rounded-[3rem] p-8 shadow-2xl relative overflow-hidden">
        <!-- Background decoration -->
        <div class="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-[#5cb83a] to-[#3a9e20]"></div>
        
        <button @click="isOtpModalOpen = false" class="absolute top-4 right-4 text-white/20 hover:text-white/40 transition-colors">
          <XCircle :size="24" />
        </button>

        <div class="text-center mb-8 mt-2">
          <div class="w-16 h-16 bg-[#5cb83a]/10 rounded-2xl flex items-center justify-center mx-auto mb-4">
            <ShieldCheck class="text-[#5cb83a]" :size="32" />
          </div>
          <h2 class="text-xl font-serif mb-2">Delivery Verification</h2>
          <p class="text-white/40 text-[10px] uppercase tracking-wider">Enter the 6-digit code from the buyer</p>
        </div>

        <!-- Error in modal -->
        <div v-if="errorMessage && isOtpModalOpen" class="mb-4 p-3 bg-red-500/10 border border-red-500/20 rounded-xl flex items-center gap-2">
          <AlertTriangle class="text-red-400 shrink-0" :size="16" />
          <p class="text-[10px] text-red-400">{{ errorMessage }}</p>
        </div>

        <input 
          v-model="otpValue" 
          type="text" 
          maxlength="6" 
          placeholder="000000"
          class="w-full bg-white/5 border border-white/10 rounded-2xl py-5 text-center text-3xl font-mono tracking-[0.3em] outline-none focus:border-[#5cb83a] transition-all mb-6" 
        />

        <div class="flex gap-3">
          <button 
            @click="isOtpModalOpen = false" 
            class="flex-1 bg-white/5 py-4 rounded-2xl text-[10px] uppercase font-bold tracking-widest hover:bg-white/10 transition-all"
          >
            Cancel
          </button>
          <button 
            @click="handleVerifyOtp" 
            :disabled="isVerifying || otpValue.length < 6"
            class="flex-[2] bg-[#5cb83a] text-[#061209] py-4 rounded-2xl text-[10px] uppercase font-bold tracking-widest flex items-center justify-center gap-2 disabled:opacity-30 hover:bg-[#4da330] transition-all"
          >
            <Loader2 v-if="isVerifying" class="animate-spin" :size="16" />
            <span v-else>Confirm Delivery</span>
          </button>
        </div>

        <p class="text-[8px] text-white/20 text-center mt-4">
          The OTP must be collected from the buyer at the delivery location
        </p>
      </div>
    </div>
  </div>
</template>

<style scoped>
.no-scrollbar::-webkit-scrollbar { display: none; }
.no-scrollbar { -ms-overflow-style: none; scrollbar-width: none; }

@keyframes slide-down {
  from { transform: translate(-50%, -20px); opacity: 0; }
  to { transform: translate(-50%, 0); opacity: 1; }
}

.animate-slide-down {
  animation: slide-down 0.3s ease-out;
}
</style>