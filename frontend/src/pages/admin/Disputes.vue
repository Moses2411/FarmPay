<script setup>
import { ref, onMounted } from 'vue';
import { RefreshCw, Loader2, AlertTriangle, ShieldAlert } from 'lucide-vue-next';
import { getAllDisputes } from '../../api/api';
import DisputeTable from './tables/DisputeTable.vue';

const disputesList = ref([]);
const isLoading = ref(true);
const currentPage = ref(1);
const totalPages = ref(1);

const fetchDisputes = async (page = 1) => {
  isLoading.value = true;
  try {
    const response = await getAllDisputes({ page: page, per_page: 20 });
    // Structure: { disputes: [], total: X, page: X, total_pages: X }
    disputesList.value = response.disputes || [];
    totalPages.value = response.total_pages || 1;
    currentPage.value = response.page || page;
  } catch (err) {
    console.error('Failed to fetch disputes:', err);
  } finally {
    isLoading.value = false;
  }
};

const handlePageChange = (newPage) => {
  if (newPage >= 1 && newPage <= totalPages.value) {
    fetchDisputes(newPage);
  }
};

onMounted(() => {
  fetchDisputes();
});
</script>

<template>
  <div class="relative min-h-100">
    <div class="flex justify-between items-center mb-8">
      <div>
        <h1 class="text-2xl font-bold text-white flex items-center gap-3">
          Dispute Resolution
        </h1>
        <p class="text-white/40 text-sm">Review and resolve conflicts between buyers and farmers.</p>
      </div>
      
      <button @click="fetchDisputes(currentPage)" class="p-2 border border-white/10 rounded-lg hover:bg-white/5 transition-colors">
        <RefreshCw :size="20" :class="{ 'animate-spin': isLoading }" class="text-white/40" />
      </button>
    </div>

    <div v-if="isLoading && disputesList.length === 0" class="flex flex-col items-center justify-center py-24 text-center">
      <div class="relative mb-4">
        <Loader2 class="animate-spin text-amber-500 absolute inset-0 m-auto" :size="32" />
      </div>
      <p class="text-white/40 font-medium">Scanning for open disputes...</p>
    </div>

    <div v-else-if="disputesList.length === 0" class="flex flex-col items-center justify-center py-24 border border-dashed border-white/10 rounded-3xl bg-white/2">
       <AlertTriangle class="text-white/10 mb-4" :size="48" />
       <p class="text-white/30 font-bold uppercase tracking-widest text-xs">No active disputes found</p>
    </div>

    <DisputeTable
      v-else
      :disputes="disputesList"
      :currentPage="currentPage"
      :totalPages="totalPages"
      @changePage="handlePageChange"
      @refresh="fetchDisputes(currentPage)"
    />
  </div>
</template>