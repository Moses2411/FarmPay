<script setup>
import { ref, onMounted } from 'vue';
import { RefreshCw, Loader2, Users } from 'lucide-vue-next';
import { getAllUsers } from '../../api/api';
import UsersTable from './tables/UsersTable.vue';

const usersList = ref([]);
const isLoading = ref(true);
const currentPage = ref(1);
const totalPages = ref(1);

const fetchUsers = async (page = 1) => {
  isLoading.value = true;
  try {
    const response = await getAllUsers({ page, per_page: 20 });
    // Based on your data structure: { users: [], total_pages: X, page: X }
    usersList.value = response.users || [];
    totalPages.value = response.total_pages || 1;
    currentPage.value = response.page || page;
  } catch (err) {
    console.error('Failed to fetch users:', err);
  } finally {
    isLoading.value = false;
  }
};

const handlePageChange = (newPage) => {
  if (newPage >= 1 && (totalPages.value === 0 || newPage <= totalPages.value)) {
    fetchUsers(newPage);
  }
};

onMounted(() => {
  fetchUsers();
});
</script>

<template>
  <div class="relative min-h-100">
    <div class="flex justify-between items-center mb-8">
      <div>
        <h1 class="text-2xl font-bold text-white flex items-center gap-3">
          User Management
        </h1>
        <p class="text-white/40 text-sm">View and manage all registered accounts on the FarmPay platform.</p>
      </div>
      
      <button @click="fetchUsers(currentPage)" class="p-2 border border-white/10 rounded-lg hover:bg-white/5 transition-colors">
        <RefreshCw :size="20" :class="{ 'animate-spin': isLoading }" class="text-white/40" />
      </button>
    </div>

    <div v-if="isLoading && usersList.length === 0" class="flex flex-col items-center justify-center py-24">
      <Loader2 class="animate-spin text-[#5cb83a] mb-4" :size="40" />
      <p class="text-white/40 font-medium">Fetching users...</p>
    </div>

    <div v-else-if="usersList.length === 0" class="flex flex-col items-center justify-center py-24 border border-dashed border-white/10 rounded-3xl bg-white/2">
       <Users class="text-white/10 mb-4" :size="48" />
       <p class="text-white/30 font-bold uppercase tracking-widest text-xs">No users found</p>
    </div>

    <UsersTable
      v-else
      :users="usersList"
      :currentPage="currentPage"
      :totalPages="totalPages"
      @changePage="handlePageChange"
    />
  </div>
</template>