<script setup>
import { ref, onMounted, computed } from 'vue';
import api from '@/api/api';
import { 
  Package, 
  ShieldCheck, 
  Clock, 
  CheckCircle2, 
  MapPin, 
  Copy, 
  Loader2,
  Inbox
} from 'lucide-vue-next';

const orders = ref([]);
const isLoading = ref(true);

// 1. Fetch Orders from Backend
const fetchOrders = async () => {
  isLoading.value = true;
  try {
    // Using your established endpoint for buyer orders
    const response = await api.get('/orders/my-orders'); 
    orders.value = response;
    console.log(orders.value)
  } catch (err) {
    console.error("Error fetching buyer orders:", err);
  } finally {
    isLoading.value = false;
  }
};

onMounted(fetchOrders);

// 2. Computed Stats based on live data
const totalSpent = computed(() => {
  return orders.value
    .filter(o => o.status === 'completed')
    .reduce((sum, o) => sum + (o.total_amount || 0), 0);
});

const inEscrow = computed(() => {
  return orders.value
    .filter(o => o.status === 'in_escrow' || o.status === 'transit')
    .reduce((sum, o) => sum + (o.total_amount || 0), 0);
});

const activeShipments = computed(() => {
  return orders.value.filter(o => o.status === 'transit').length;
});

// Helper to copy OTP
const copyOTP = (otp) => {
  if (!otp) return;
  navigator.clipboard.writeText(otp.replace(/\s/g, ''));
  alert("OTP Copied to clipboard!");
};
</script>

<template>
  <div class="min-h-screen bg-[#061209] text-[#f0ede4] p-6 md:p-10">
    <div class="max-w-5xl mx-auto">
      
      <header class="mb-10 flex justify-between items-end">
        <div>
          <h1 class="text-3xl font-serif">Buyer Dashboard</h1>
          <p class="text-white/40 text-sm">Track your produce and manage delivery codes.</p>
        </div>
        <div class="hidden md:block text-right">
           <span class="text-[10px] uppercase text-[#5cb83a] font-bold tracking-widest block">Escrow Status</span>
           <span class="text-xs opacity-40 italic">Active Protection Enabled</span>
        </div>
      </header>

      <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12">
        <div class="bg-white/5 border border-white/10 p-6 rounded-[2.5rem]">
          <p class="text-[10px] uppercase tracking-widest text-white/30 font-bold mb-2">Total Spent</p>
          <p class="text-3xl font-serif">₦{{ totalSpent.toLocaleString() }}</p>
        </div>
        <div class="bg-[#5cb83a]/10 border border-[#5cb83a]/20 p-6 rounded-[2.5rem] relative overflow-hidden">
          <ShieldCheck class="absolute -right-4 -bottom-4 text-[#5cb83a]/10" :size="100" />
          <p class="text-[10px] uppercase tracking-widest text-[#5cb83a] font-bold mb-2">Secured In Escrow</p>
          <p class="text-3xl font-serif">₦{{ inEscrow.toLocaleString() }}</p>
        </div>
        <div class="bg-white/5 border border-white/10 p-6 rounded-[2.5rem]">
          <p class="text-[10px] uppercase tracking-widest text-white/30 font-bold mb-2">Active Shipments</p>
          <p class="text-3xl font-serif">{{ activeShipments }}</p>
        </div>
      </div>

      <section class="space-y-6">
        <h3 class="font-bold flex items-center gap-2 text-xs uppercase tracking-[0.2em] text-white/40 ml-2">
           Recent Orders
        </h3>

        <div v-if="isLoading" class="flex flex-col items-center justify-center py-20 bg-white/2 rounded-[2.5rem] border border-white/5">
          <Loader2 class="animate-spin text-[#5cb83a] mb-4" :size="32" />
          <p class="text-xs uppercase tracking-widest opacity-40">Loading Orders...</p>
        </div>

        <div v-else-if="orders.length === 0" class="flex flex-col items-center justify-center py-20 bg-white/2 rounded-[2.5rem] border border-white/5 text-white/20">
          <Inbox :size="48" class="mb-4" />
          <p class="font-serif text-lg">No orders found</p>
          <p class="text-xs uppercase tracking-wider">Your purchases will appear here</p>
        </div>

        <div v-else v-for="order in orders" :key="order.id" 
             class="bg-[#0d2010] border border-white/10 rounded-[2.5rem] p-6 flex flex-col md:flex-row items-center gap-6 transition-all hover:border-[#5cb83a]/30">
          
          <div class="w-20 h-20 rounded-2xl bg-black/20 border border-white/5 flex items-center justify-center overflow-hidden">
            <img v-if="order.product_image" :src="order.product_image" class="w-full h-full object-cover" />
            <Package v-else class="text-white/10" :size="32" />
          </div>

          <div class="flex-1 space-y-1 text-center md:text-left">
            <div class="flex flex-col md:flex-row md:items-center gap-2">
              <span class="text-[10px] font-mono text-white/20 uppercase tracking-tighter">#{{ order.id.slice(-8) }}</span>
              <h4 class="font-bold text-lg leading-tight">{{ order.product_name || 'Farm Produce' }}</h4>
            </div>
            <p class="text-sm text-white/40">Status: <span class="text-white/70 capitalize">{{ order.status.replace('_', ' ') }}</span></p>
            
            <div class="mt-2 inline-flex items-center gap-2 px-3 py-1 rounded-full bg-black/30 border border-white/5">
              <div v-if="order.status === 'in_escrow'" class="flex items-center gap-1.5 text-amber-500 font-bold text-[10px] uppercase">
                <Clock :size="12" /> Funds Locked
              </div>
              <div v-else-if="order.status === 'transit'" class="flex items-center gap-1.5 text-blue-400 font-bold text-[10px] uppercase">
                <MapPin :size="12" /> Dispatched
              </div>
              <div v-else class="flex items-center gap-1.5 text-[#5cb83a] font-bold text-[10px] uppercase">
                <CheckCircle2 :size="12" /> Completed
              </div>
            </div>
          </div>

          <div v-if="order.status !== 'completed'" class="bg-black/40 border border-[#5cb83a]/20 p-5 rounded-3xl text-center min-w-[200px]">
            <span class="text-[9px] uppercase tracking-widest text-[#5cb83a] font-bold block mb-2">Delivery Release Code</span>
            <div class="flex items-center justify-center gap-3">
               <span class="text-2xl font-mono font-bold tracking-widest text-[#f0ede4]">{{ order.otp_code || '--- ---' }}</span>
               <button v-if="order.otp_code" @click="copyOTP(order.otp_code)" class="text-white/20 hover:text-[#5cb83a] transition-colors">
                 <Copy :size="16" />
               </button>
            </div>
            <p class="text-[9px] text-white/30 mt-2 italic leading-tight">Read this to the rider only after <br/> checking your items.</p>
          </div>

          <div v-else class="px-8 text-right">
             <span class="text-[10px] text-white/20 block uppercase font-bold">Total Paid</span>
             <span class="text-2xl font-serif">₦{{ (order.total_amount || 0).toLocaleString() }}</span>
          </div>

        </div>
      </section>

    </div>
  </div>
</template>