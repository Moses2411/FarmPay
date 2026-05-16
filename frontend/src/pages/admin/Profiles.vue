<script setup>
import { ref, onMounted } from 'vue';
import { RefreshCw, Loader2, Leaf, Search } from 'lucide-vue-next';
import { getFarmersProfile } from '../../api/api';
import ProfileTable from './tables/ProfileTable.vue';

const farmersList = ref([]);
const totalCount = ref(0);
const isLoading = ref(true);
const currentPage = ref(1);
const totalPages = ref(1);

const fetchFarmers = async (page = 1) => {
  isLoading.value = true;
  try {
    const response = await getFarmersProfile({ page: page, per_page: 20 });
    // Based on your data structure: { farmer_profiles: [], total: X, total_pages: X }
    farmersList.value = response.farmer_profiles || [];
    totalCount.value = response.total || 0;
    totalPages.value = response.total_pages || 1;
    currentPage.value = response.page || page;
  } catch (err) {
    console.error('Failed to fetch farmer profiles:', err);
  } finally {
    isLoading.value = false;
  }
};

const handlePageChange = (newPage) => {
  if (newPage >= 1 && newPage <= totalPages.value) {
    fetchFarmers(newPage);
  }
};

onMounted(() => {
  fetchFarmers();
});
</script>

<template>
  <div class="relative min-h-100">
    <div class="flex justify-between items-center mb-8">
      <div>
        <h1 class="text-2xl font-bold text-white flex items-center gap-3">
          Farmer Profiles
        </h1>
        <p class="text-white/40 text-sm">Verify and manage business identities for platform producers.</p>
      </div>
      
      <button @click="fetchFarmers(currentPage)" class="p-2 border border-white/10 rounded-lg hover:bg-white/5 transition-colors">
        <RefreshCw :size="20" :class="{ 'animate-spin': isLoading }" class="text-white/40" />
      </button>
    </div>

    <div v-if="isLoading && farmersList.length === 0" class="flex flex-col items-center justify-center py-24">
      <Loader2 class="animate-spin text-[#5cb83a] mb-4" :size="40" />
      <p class="text-white/40 font-medium">Loading farmer directory...</p>
    </div>

    <div v-else-if="farmersList.length === 0" class="flex flex-col items-center justify-center py-24 border border-dashed border-white/10 rounded-3xl bg-white/2">
       <Leaf class="text-white/10 mb-4" :size="48" />
       <p class="text-white/30 font-bold uppercase tracking-widest text-xs">No farmer profiles registered</p>
    </div>

    <ProfileTable
      v-else
      :farmers="farmersList"
      :total="totalCount"
      :currentPage="currentPage"
      :totalPages="totalPages"
      @changePage="handlePageChange"
    />
  </div>
</template>