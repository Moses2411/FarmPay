<script setup>
import { ref, onMounted } from 'vue';
import { RefreshCw, Loader2, Package } from 'lucide-vue-next';
import { getAllOrders } from '../../api/api';
import OrderTable from './tables/OrderTable.vue';

// States
const ordersList = ref([]);
const isLoading = ref(true);
const currentPage = ref(1);
const totalPages = ref(1);

const fetchOrders = async (page = 1) => {
  isLoading.value = true;
  try {
    const response = await getAllOrders({ page: page, per_page: 20 });
    console.log("API Response:", response);

    ordersList.value = response.orders || []; 
    
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
        <h1 class="text-2xl font-bold text-white">Orders Management</h1>
        <p class="text-white/40 text-sm">Track and manage customer orders across the platform.</p>
      </div>
      
      <button @click="fetchOrders(currentPage)" class="p-2 border border-white/10 rounded-lg hover:bg-white/5 transition-colors">
        <RefreshCw :size="20" :class="{ 'animate-spin': isLoading }" class="text-white/40" />
      </button>
    </div>

    <div v-if="isLoading && ordersList.length === 0" class="flex flex-col items-center justify-center py-24">
      <Loader2 class="animate-spin text-[#5cb83a] mb-4" :size="40" />
      <p class="text-white/40 font-medium">Fetching orders...</p>
    </div>

    <div v-else>
      <OrderTable
        :orders="ordersList" 
        :currentPage="currentPage"
        :totalPages="totalPages"
        @changePage="handlePageChange"
        @view="(order) => console.log('Viewing order:', order.id)"
      />
    </div>
  </div>
</template>