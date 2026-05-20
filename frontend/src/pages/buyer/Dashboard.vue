<script setup>
import { ref, onMounted, computed } from 'vue';
import { useRouter } from 'vue-router';
import { useAuthStore } from '../../stores/auth';
import api from '@/api/api';
import {
  Package, ShieldCheck, Loader2, CheckCircle2,
  MapPin, Copy, Inbox, LayoutDashboard,
  ShoppingBag, LogOut, RotateCw, Truck, Clock
} from 'lucide-vue-next';
import LiveMap from '@/components/logistics/LiveMap.vue';
import DeliveryTimeline from '@/components/logistics/DeliveryTimeline.vue';

const router = useRouter();
const auth = useAuthStore();
const orders = ref([]);
const isLoading = ref(true);

const isTrackingModalOpen = ref(false);
const trackingOrder = ref(null);

const user = ref({
  name: auth.user?.fullName?.split(' ')[0] || 'User',
  email: auth.user?.email,
  avatar: null,
  role: auth.user?.role || 'buyer'
});

const fetchOrders = async () => {
  isLoading.value = true;
  try {
    orders.value = await api.get('/orders/my-orders');
  } catch (err) {
    console.error("Error fetching orders:", err);
  } finally {
    isLoading.value = false;
  }
};

const openTrackingModal = (order) => {
  trackingOrder.value = order;
  isTrackingModalOpen.value = true;
};

const handleLogout = () => {
  auth.logout();
  router.push('/login');
};

const copyOTP = (otp) => {
  if (!otp) return;
  navigator.clipboard.writeText(otp.replace(/\s/g, ''));
};

onMounted(fetchOrders);

const totalSpent = computed(() => {
  return orders.value
    .filter(o => o.status === 'completed')
    .reduce((sum, o) => sum + (Number(o.total_amount) || 0), 0);
});

const inEscrow = computed(() => {
  return orders.value
    .filter(o => o.escrow_status === 'held')
    .reduce((sum, o) => sum + (Number(o.total_amount) || 0), 0);
});

const inTransit = computed(() => {
  return orders.value.filter(o =>
    o.delivery_status === 'in_transit' ||
    o.delivery_status === 'transit' ||
    o.delivery_status === 'assigned'
  ).length;
});

const pendingPayment = computed(() => {
  return orders.value.filter(o => o.status === 'pending').length;
});

const getOrderItems = (order) => {
  if (order.items && order.items.length > 0) {
    return order.items.map(item => item.product?.name || 'Produce').join(', ');
  }
  return 'Produce Order';
};

const getStatusLabel = (order) => {
  if (order.status === 'pending') return 'Payment Pending';
  if (order.delivery_status === 'in_transit' || order.delivery_status === 'transit') return 'In Transit';
  if (order.status === 'completed') return 'Completed';
  return order.delivery_status || order.status || 'N/A';
};

const getStatusColor = (order) => {
  if (order.status === 'pending') return 'bg-amber-500/10 text-amber-500';
  if (order.delivery_status === 'in_transit' || order.delivery_status === 'transit') return 'bg-blue-500/10 text-blue-400';
  if (order.status === 'completed') return 'bg-[#5cb83a]/10 text-[#5cb83a]';
  return 'bg-white/10 text-white/60';
};
</script>

<template>
  <div class="flex min-h-screen bg-[#061209] text-[#f0ede4]">

    <aside class="w-64 border-r border-white/5 bg-[#081a0c] hidden md:flex flex-col p-6 sticky top-0 h-screen">
      <div class="mb-10 flex items-center gap-2 px-2 cursor-pointer" @click="router.push('/')">
        <div class="w-8 h-8 bg-[#5cb83a] rounded-lg flex items-center justify-center">
          <ShieldCheck class="text-[#061209]" :size="20" />
        </div>
        <span class="font-serif text-xl font-bold tracking-tight">FarmPay</span>
      </div>

      <nav class="flex-1 space-y-2">
        <button class="w-full flex items-center gap-3 px-4 py-3 rounded-2xl bg-[#5cb83a]/10 text-[#5cb83a] font-medium">
          <LayoutDashboard :size="20" /> Dashboard
        </button>
        <button @click="router.push('/marketplace')" class="w-full flex items-center gap-3 px-4 py-3 rounded-2xl hover:bg-white/5 text-white/40 hover:text-white transition-all">
          <ShoppingBag :size="20" /> Marketplace
        </button>
      </nav>

      <div class="mt-auto pt-6 border-t border-white/5">
        <div class="flex items-center gap-3 mb-4 px-2">
          <div class="w-10 h-10 rounded-full bg-[#5cb83a]/20 border border-[#5cb83a]/30 flex items-center justify-center text-[#5cb83a] font-bold">
            {{ user.name.charAt(0) }}
          </div>
          <div class="overflow-hidden">
            <p class="text-sm font-bold truncate">{{ user.name }}</p>
            <p class="text-[10px] text-white/30 uppercase tracking-widest">{{ user.role }}</p>
          </div>
        </div>
        <button @click="handleLogout" class="w-full flex items-center gap-3 px-4 py-3 rounded-2xl text-red-400 hover:bg-red-400/10 transition-all text-sm font-medium">
          <LogOut :size="18" /> Logout
        </button>
      </div>
    </aside>

    <main class="flex-1 p-6 md:p-10 overflow-y-auto">
      <div class="max-w-5xl mx-auto">

        <header class="mb-10 flex justify-between items-center">
          <div>
            <h1 class="text-3xl font-serif">Buyer Terminal</h1>
            <p class="text-white/40 text-sm italic">Secure produce acquisition & escrow management.</p>
          </div>
          <button @click="fetchOrders" class="p-3 rounded-full bg-white/5 border border-white/10 hover:border-[#5cb83a] transition-all">
            <RotateCw :size="18" :class="{ 'animate-spin': isLoading }" />
          </button>
        </header>

        <div class="grid grid-cols-1 md:grid-cols-4 gap-4 mb-12">
          <div class="bg-white/5 border border-white/10 p-5 rounded-[2rem]">
            <p class="text-[10px] uppercase tracking-widest text-white/30 font-bold mb-2">Total Settled</p>
            <p class="text-2xl font-serif">₦{{ totalSpent.toLocaleString() }}</p>
          </div>
          <div class="bg-[#5cb83a]/10 border border-[#5cb83a]/20 p-5 rounded-[2rem] relative overflow-hidden">
            <ShieldCheck class="absolute -right-4 -bottom-4 text-[#5cb83a]/5" :size="80" />
            <p class="text-[10px] uppercase tracking-widest text-[#5cb83a] font-bold mb-2">Active Escrow</p>
            <p class="text-2xl font-serif">₦{{ inEscrow.toLocaleString() }}</p>
          </div>
          <div class="bg-blue-500/10 border border-blue-500/20 p-5 rounded-[2rem]">
            <p class="text-[10px] uppercase tracking-widest text-blue-400 font-bold mb-2">In Transit</p>
            <p class="text-2xl font-serif">{{ inTransit }}</p>
          </div>
          <div class="bg-amber-500/10 border border-amber-500/20 p-5 rounded-[2rem]">
            <p class="text-[10px] uppercase tracking-widest text-amber-500 font-bold mb-2">Pending Payment</p>
            <p class="text-2xl font-serif">{{ pendingPayment }}</p>
          </div>
        </div>

        <section class="space-y-6">
          <h3 class="font-bold text-xs uppercase tracking-[0.2em] text-white/40 px-2">Order History</h3>

          <div v-if="isLoading" class="flex flex-col items-center justify-center py-20">
            <Loader2 class="animate-spin text-[#5cb83a]" :size="32" />
          </div>

          <div v-else-if="orders.length === 0" class="text-center py-20 bg-white/2 rounded-[2.5rem] border border-white/5">
            <Inbox :size="40" class="mx-auto mb-4 text-white/10" />
            <p class="text-white/40">No orders found.</p>
            <button @click="router.push('/marketplace')" class="mt-4 text-[#5cb83a] text-sm font-bold hover:underline">
              Browse Marketplace
            </button>
          </div>

          <div v-else v-for="order in orders" :key="order.id"
               class="bg-[#0d2010] border border-white/10 rounded-[2.5rem] p-6 transition-all hover:bg-[#112814]">

            <div class="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-4">
              <div class="flex items-center gap-4">
                <div class="w-14 h-14 rounded-2xl bg-black/20 border border-white/5 flex items-center justify-center">
                  <Package class="text-[#5cb83a]/40" :size="24" />
                </div>
                <div>
                  <span class="text-[9px] font-mono text-white/20 uppercase block mb-1">#{{ order.id?.slice(-8) }}</span>
                  <h4 class="font-bold text-lg">{{ getOrderItems(order) }}</h4>
                </div>
              </div>

              <div class="flex items-center gap-3">
                <span
                  class="px-3 py-1.5 rounded-lg text-[8px] font-bold uppercase tracking-wider"
                  :class="getStatusColor(order)"
                >
                  {{ getStatusLabel(order) }}
                </span>
              </div>
            </div>

            <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4 pb-4 border-b border-white/5">
              <div>
                <p class="text-[8px] uppercase text-white/30 font-bold mb-1">Delivery To</p>
                <p class="text-xs text-white/60">{{ order.delivery_address || order.delivery_location || 'Not specified' }}</p>
              </div>
              <div>
                <p class="text-[8px] uppercase text-white/30 font-bold mb-1">Delivery Fee</p>
                <p class="text-xs text-white/60">₦{{ (order.delivery_fee || 0).toLocaleString() }}</p>
              </div>
              <div>
                <p class="text-[8px] uppercase text-white/30 font-bold mb-1">Escrow Status</p>
                <p class="text-xs" :class="order.escrow_status === 'held' ? 'text-amber-400' : 'text-[#5cb83a]'">
                  {{ order.escrow_status || 'N/A' }}
                </p>
              </div>
              <div>
                <p class="text-[8px] uppercase text-white/30 font-bold mb-1">Total Amount</p>
                <p class="text-sm font-serif text-[#5cb83a]">₦{{ (order.total_amount || 0).toLocaleString() }}</p>
              </div>
            </div>

            <div class="flex flex-wrap gap-3">
              <button
                v-if="order.status === 'pending'"
                @click="openTrackingModal(order)"
                class="bg-[#5cb83a] text-[#061209] px-5 py-2.5 rounded-xl text-[10px] font-bold uppercase tracking-widest flex items-center gap-2 hover:bg-[#4da330] transition-all"
              >
                <Clock :size="14" />
                Pending - View Order
              </button>

              <button
                v-if="order.delivery_status === 'in_transit' || order.delivery_status === 'transit'"
                @click="openTrackingModal(order)"
                class="bg-blue-500/10 text-blue-400 border border-blue-500/20 px-5 py-2.5 rounded-xl text-[10px] font-bold uppercase tracking-widest flex items-center gap-2 hover:bg-blue-500/20 transition-all"
              >
                <Truck :size="14" />
                Track Delivery
              </button>

              <div v-if="order.otp_code && order.status !== 'completed' && order.delivery_status !== 'disputed'"
                   class="bg-black/40 border border-[#5cb83a]/20 px-5 py-2.5 rounded-xl">
                <span class="text-[8px] uppercase tracking-widest text-[#5cb83a] font-bold block mb-1">Release Code</span>
                <div class="flex items-center gap-3">
                  <span class="text-lg font-mono font-bold">{{ order.otp_code }}</span>
                  <button @click="copyOTP(order.otp_code)" class="text-white/30 hover:text-[#5cb83a]">
                    <Copy :size="14" />
                  </button>
                </div>
              </div>

              <div v-if="order.status === 'completed'" class="flex items-center gap-2 text-[#5cb83a]">
                <CheckCircle2 :size="18" />
                <span class="text-[10px] font-bold uppercase">Delivered & Paid</span>
              </div>
            </div>
          </div>
        </section>
      </div>
    </main>

    <!-- Tracking Modal -->
    <div v-if="isTrackingModalOpen" class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-[#061209]/95 backdrop-blur-md">
      <div class="bg-[#0d2010] border border-white/10 w-full max-w-2xl rounded-[3rem] p-8 shadow-2xl max-h-[90vh] overflow-y-auto">
        <div class="flex justify-between items-center mb-6">
          <h2 class="text-xl font-serif">Track Your Delivery</h2>
          <button @click="isTrackingModalOpen = false" class="text-white/20 hover:text-white">
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
          </button>
        </div>

        <div class="space-y-6">
          <LiveMap
            :origin="{ coordinates: [7.4386, 11.0626], name: 'Kaduna' }"
            :destination="{ coordinates: [7.4250, 11.0580], name: trackingOrder?.delivery_address }"
            :status="trackingOrder?.delivery_status || 'pending'"
          />

          <DeliveryTimeline :current-status="trackingOrder?.delivery_status || 'pending'" />
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.no-scrollbar::-webkit-scrollbar { display: none; }
</style>