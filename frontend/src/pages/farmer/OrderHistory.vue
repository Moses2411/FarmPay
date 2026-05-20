<script setup>
import { ref, onMounted } from 'vue';
import api from '@/api/api';
import {
  Package, Loader2, Clock, CheckCircle2,
  AlertCircle, MapPin, User, Phone, ChevronRight,
  Truck, Calendar
} from 'lucide-vue-next';

const isLoading = ref(true);
const orders = ref([]);

const fetchOrders = async () => {
  isLoading.value = true;
  try {
    orders.value = await api.get('/orders/farmer-orders');
  } catch (err) {
    console.error("Failed to fetch orders:", err);
  } finally {
    isLoading.value = false;
  }
};

const formatCurrency = (value) => {
  return new Intl.NumberFormat('en-NG', { style: 'currency', currency: 'NGN', minimumFractionDigits: 0 }).format(value);
};

const formatDate = (dateStr) => {
  if (!dateStr) return 'N/A';
  return new Date(dateStr).toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' });
};

const getStatusConfig = (status) => {
  const configs = {
    'pending': { color: 'text-amber-500', bg: 'bg-amber-500/10', label: 'Pending Payment' },
    'paid': { color: 'text-blue-400', bg: 'bg-blue-500/10', label: 'Paid - Awaiting Pickup' },
    'in_transit': { color: 'text-purple-400', bg: 'bg-purple-500/10', label: 'In Transit' },
    'completed': { color: 'text-[#5cb83a]', bg: 'bg-[#5cb83a]/10', label: 'Completed' },
    'disputed': { color: 'text-red-400', bg: 'bg-red-500/10', label: 'Disputed' },
  };
  return configs[status] || configs.pending;
};

onMounted(fetchOrders);
</script>

<template>
  <div class="min-h-screen bg-[#061209] text-[#f0ede4] p-6 md:p-8">
    <div class="max-w-6xl mx-auto">
      <!-- Header -->
      <div class="mb-8">
        <h1 class="text-3xl font-serif">Order History</h1>
        <p class="text-white/40 text-sm">Track all your orders and sales</p>
      </div>

      <!-- Stats Summary -->
      <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
        <div class="bg-white/5 border border-white/10 p-4 rounded-xl">
          <p class="text-[10px] text-white/40 uppercase mb-1">Total Orders</p>
          <p class="text-2xl font-serif">{{ orders.length }}</p>
        </div>
        <div class="bg-[#5cb83a]/10 border border-[#5cb83a]/20 p-4 rounded-xl">
          <p class="text-[10px] text-[#5cb83a] uppercase mb-1">Completed</p>
          <p class="text-2xl font-serif text-[#5cb83a]">{{ orders.filter(o => o.status === 'completed').length }}</p>
        </div>
        <div class="bg-blue-500/10 border border-blue-500/20 p-4 rounded-xl">
          <p class="text-[10px] text-blue-400 uppercase mb-1">In Transit</p>
          <p class="text-2xl font-serif text-blue-400">{{ orders.filter(o => o.delivery_status === 'in_transit').length }}</p>
        </div>
        <div class="bg-amber-500/10 border border-amber-500/20 p-4 rounded-xl">
          <p class="text-[10px] text-amber-500 uppercase mb-1">Pending</p>
          <p class="text-2xl font-serif text-amber-500">{{ orders.filter(o => o.status === 'pending' || o.status === 'paid').length }}</p>
        </div>
      </div>

      <!-- Loading State -->
      <div v-if="isLoading" class="flex justify-center py-20">
        <Loader2 class="animate-spin text-[#5cb83a]" :size="40" />
      </div>

      <!-- Empty State -->
      <div v-else-if="orders.length === 0" class="text-center py-20 bg-white/2 rounded-[3rem] border border-dashed border-white/10">
        <Package class="mx-auto mb-4 text-white/10" :size="64" />
        <p class="text-white/40 text-lg mb-2">No orders yet</p>
        <p class="text-white/20 text-sm">Orders will appear here when buyers purchase your products</p>
      </div>

      <!-- Orders List -->
      <div v-else class="space-y-4">
        <div 
          v-for="order in orders" 
          :key="order.order_id"
          class="bg-[#0d2010] border border-white/10 rounded-2xl overflow-hidden hover:border-[#5cb83a]/30 transition-all"
        >
          <!-- Order Header -->
          <div class="p-4 flex justify-between items-center border-b border-white/5">
            <div class="flex items-center gap-3">
              <div class="p-2 bg-white/5 rounded-xl">
                <Package class="text-[#5cb83a]" :size="18" />
              </div>
              <div>
                <p class="text-sm font-medium">Order #{{ order.order_id?.slice(-8).toUpperCase() }}</p>
                <p class="text-[10px] text-white/40 flex items-center gap-1">
                  <Calendar :size="10" /> {{ formatDate(order.created_at) }}
                </p>
              </div>
            </div>
            <span 
              class="px-3 py-1 rounded-lg text-[10px] font-bold uppercase"
              :class="[getStatusConfig(order.status).bg, getStatusConfig(order.status).color]"
            >
              {{ getStatusConfig(order.status).label }}
            </span>
          </div>

          <!-- Order Details -->
          <div class="p-4 grid grid-cols-1 md:grid-cols-3 gap-4">
            <!-- Items -->
            <div>
              <p class="text-[10px] text-white/40 uppercase mb-2">Items</p>
              <div v-for="item in order.items" :key="item.product_id" class="flex justify-between text-sm mb-1">
                <span>{{ item.product_name }} x{{ item.quantity }}</span>
                <span class="text-[#5cb83a]">{{ formatCurrency(item.price * item.quantity) }}</span>
              </div>
            </div>

            <!-- Buyer Info -->
            <div>
              <p class="text-[10px] text-white/40 uppercase mb-2">Buyer</p>
              <div class="flex items-center gap-2 text-sm">
                <User :size="14" class="text-white/40" />
                <span>{{ order.buyer_name }}</span>
              </div>
              <div class="flex items-center gap-2 text-sm mt-1">
                <Phone :size="14" class="text-white/40" />
                <span>{{ order.buyer_phone }}</span>
              </div>
            </div>

            <!-- Delivery -->
            <div>
              <p class="text-[10px] text-white/40 uppercase mb-2">Delivery</p>
              <div class="flex items-center gap-2 text-sm">
                <MapPin :size="14" class="text-white/40" />
                <span>{{ order.delivery_address }}</span>
              </div>
              <p class="text-xs text-white/40 mt-1">Fee: {{ formatCurrency(order.delivery_fee) }}</p>
            </div>
          </div>

          <!-- Order Footer -->
          <div class="p-4 bg-white/5 flex justify-between items-center">
            <div>
              <p class="text-[10px] text-white/40 uppercase">Total Amount</p>
              <p class="text-xl font-serif text-[#5cb83a]">{{ formatCurrency(order.total_amount) }}</p>
            </div>
            <button class="px-4 py-2 bg-white/5 hover:bg-white/10 rounded-xl text-xs font-bold uppercase flex items-center gap-2">
              View Details
              <ChevronRight :size="14" />
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>