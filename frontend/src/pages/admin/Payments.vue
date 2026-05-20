<script setup>
import { ref, onMounted } from 'vue';
import { RefreshCw, Loader2, CreditCard, Search, Receipt } from 'lucide-vue-next';
import { getAllPayment } from '../../api/api';
import PaymentTable from './tables/PaymentTable.vue';

const paymentsList = ref([]);
const isLoading = ref(true);
const currentPage = ref(1);
const totalPages = ref(1);

const fetchPayments = async (page = 1) => {
  isLoading.value = true;
  try {
    const response = await getAllPayment({ page: page, per_page: 20 });
    // Structure: { payments: [], total: X, page: X, total_pages: X }
    paymentsList.value = response.payments || [];
    totalPages.value = response.total_pages || 1;
    currentPage.value = response.page || page;
  } catch (err) {
    console.error('Failed to fetch payments:', err);
  } finally {
    isLoading.value = false;
  }
};

const handlePageChange = (newPage) => {
  if (newPage >= 1 && newPage <= totalPages.value) {
    fetchPayments(newPage);
  }
};

onMounted(() => {
  fetchPayments();
});
</script>

<template>
  <div class="relative min-h-100">
    <div class="flex justify-between items-center mb-8">
      <div>
        <h1 class="text-2xl font-bold text-white flex items-center gap-3">
          Financial Transactions
        </h1>
        <p class="text-white/40 text-sm">Monitor all platform payments and escrow holdings.</p>
      </div>
      
      <div class="flex gap-3">
        <button @click="fetchPayments(currentPage)" class="p-2 border border-white/10 rounded-lg hover:bg-white/5 transition-colors">
          <RefreshCw :size="20" :class="{ 'animate-spin': isLoading }" class="text-white/40" />
        </button>
      </div>
    </div>


    <div v-if="isLoading && paymentsList.length === 0" class="flex flex-col items-center justify-center py-24 text-center">
      <div class="relative mb-4">
        <Loader2 class="animate-spin text-[#5cb83a] absolute inset-0 m-auto" :size="32" />
      </div>
      <p class="text-white/40 font-medium">Loading ledger records...</p>
    </div>

    <div v-else-if="paymentsList.length === 0" class="flex flex-col items-center justify-center py-24 border border-dashed border-white/10 rounded-3xl bg-white/2">
       <Receipt class="text-white/10 mb-4" :size="48" />
       <p class="text-white/30 font-bold uppercase tracking-widest text-xs">No payment history found</p>
    </div>

    <PaymentTable 
      v-else
      :payments="paymentsList"
      :currentPage="currentPage"
      :totalPages="totalPages"
      @changePage="handlePageChange"
    />
  </div>
</template>