<script setup>
import { ref, onMounted } from 'vue';
import { RefreshCw, Loader2, ShoppingBag, AlertTriangle } from 'lucide-vue-next';
import { getAllOrders } from '../../api/api';
import OrderTable from './tables/OrderTable.vue';

const ordersList = ref([]);
const isLoading = ref(true);
const currentPage = ref(1);
const totalPages = ref(1);
const totalOrders = ref(0);

const fetchOrders = async (page = 1) => {
  isLoading.value = true;
  try {
    const response = await getAllOrders({ page: page, per_page: 20 });
    // Structure expected: { orders: [], total: X, page: X, total_pages: X }
    ordersList.value = response.orders || [];
    totalOrders.value = response.total || 0;
    totalPages.value = response.total_pages || 1;
    currentPage.value = response.page || page;
  } catch (err) {
    console.error('Failed to fetch orders:', err);
  } finally {
    isLoading.value = false;
  }
};

const handlePageChange = (newPage) => {
  if (newPage >= 1 && newPage <= totalPages.value) {
    fetchOrders(newPage);
  }
};

onMounted(() => {
  fetchOrders();
});
</script>

<template>
  <div class="relative min-h-100">
    <div class="flex justify-between items-center mb-8">
      <div>
        <h1 class="text-2xl font-bold text-white flex items-center gap-3">
          Orders Management
        </h1>
        <p class="text-white/40 text-sm">Track and manage customer orders across the platform.</p>
      </div>
      
      <button @click="fetchOrders(currentPage)" class="p-2 border border-white/10 rounded-lg hover:bg-white/5 transition-colors">
        <RefreshCw :size="20" :class="{ 'animate-spin': isLoading }" class="text-white/40" />
      </button>
    </div>

    <div v-if="isLoading && ordersList.length === 0" class="flex flex-col items-center justify-center py-24 text-center">
      <Loader2 class="animate-spin text-[#5cb83a] mb-4" :size="40" />
      <p class="text-white/40 font-medium">Fetching platform orders...</p>
    </div>

    <div v-else-if="ordersList.length === 0" class="flex flex-col items-center justify-center py-24 border border-dashed border-white/10 rounded-3xl bg-white/2">
       <ShoppingBag class="text-white/10 mb-4" :size="48" />
       <p class="text-white/30 font-bold uppercase tracking-widest text-xs">No orders placed yet</p>
    </div>

    <OrderTable
      v-else
      :orders="ordersList" 
      :currentPage="currentPage"
      :totalPages="totalPages"
      @changePage="handlePageChange"
    />
  </div>
</template>