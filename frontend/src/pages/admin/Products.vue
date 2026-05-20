<script setup>
import { ref, onMounted } from 'vue';
import { RefreshCw, Loader2, Package, Search, Tag } from 'lucide-vue-next';
import { getAllProducts } from '../../api/api';
import ProductTable from './tables/ProductTable.vue';

const productsList = ref([]);
const isLoading = ref(true);
const currentPage = ref(1);
const totalPages = ref(1);
const totalProducts = ref(0);

const fetchProducts = async (page = 1) => {
  isLoading.value = true;
  try {
    const response = await getAllProducts({ page: page, per_page: 20 });
    // Structure: { products: [], total: X, page: X, total_pages: X }
    productsList.value = response.products || [];
    totalProducts.value = response.total || 0;
    totalPages.value = response.total_pages || 1;
    currentPage.value = response.page || page;
  } catch (err) {
    console.error('Failed to fetch products:', err);
  } finally {
    isLoading.value = false;
  }
};

const handlePageChange = (newPage) => {
  if (newPage >= 1 && newPage <= totalPages.value) {
    fetchProducts(newPage);
  }
};

onMounted(() => {
  fetchProducts();
});
</script>

<template>
  <div class="relative min-h-100">
    <div class="flex justify-between items-center mb-8">
      <div>
        <h1 class="text-2xl font-bold text-white flex items-center gap-3">
          Product Catalog
        </h1>
        <p class="text-white/40 text-sm">Monitor inventory, pricing, and quality scan results.</p>
      </div>
      
      <div class="flex gap-3">
        <button @click="fetchProducts(currentPage)" class="p-2 border border-white/10 rounded-lg hover:bg-white/5 transition-colors">
          <RefreshCw :size="20" :class="{ 'animate-spin': isLoading }" class="text-white/40" />
        </button>
      </div>
    </div>

    <div v-if="isLoading && productsList.length === 0" class="flex flex-col items-center justify-center py-24 text-center">
      <Loader2 class="animate-spin text-[#5cb83a] mb-4" :size="40" />
      <p class="text-white/40 font-medium">Loading store inventory...</p>
    </div>

    <div v-else-if="productsList.length === 0" class="flex flex-col items-center justify-center py-24 border border-dashed border-white/10 rounded-3xl bg-white/2">
       <Package class="text-white/10 mb-4" :size="48" />
       <p class="text-white/30 font-bold uppercase tracking-widest text-xs">No products listed yet</p>
    </div>

    <ProductTable
      v-else
      :products="productsList"
      :currentPage="currentPage"
      :totalPages="totalPages"
      @changePage="handlePageChange"
    />
  </div>
</template>