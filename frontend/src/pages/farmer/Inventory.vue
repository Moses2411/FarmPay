<script setup>
import { ref, onMounted } from 'vue';
import { getMyProducts, deleteProduct } from '@/api/api';
import { 
  Package, Plus, Trash2, Loader2,
  RefreshCw, Eye, AlertTriangle
} from 'lucide-vue-next';

const products = ref([]);
const isLoading = ref(true);
const isDeleting = ref(null);
const deleteError = ref('');

const fetchProducts = async () => {
  isLoading.value = true;
  try {
    products.value = await getMyProducts();
  } catch (err) {
    console.error("Failed to fetch products:", err);
  } finally {
    isLoading.value = false;
  }
};

const handleDelete = async (productId) => {
  if (!confirm('Are you sure you want to delete this product?')) return;

  isDeleting.value = productId;
  try {
    await deleteProduct(productId);
    products.value = products.value.filter(p => p.id !== productId);
  } catch (err) {
    deleteError.value = err.detail || "Cannot delete - product may have orders";
    setTimeout(() => deleteError.value = '', 3000);
  } finally {
    isDeleting.value = null;
  }
};

const formatCurrency = (value) => {
  return new Intl.NumberFormat('en-NG', { style: 'currency', currency: 'NGN' }).format(value);
};

onMounted(fetchProducts);
</script>

<template>
  <div class="min-h-screen bg-[#061209] text-[#f0ede4] p-6 md:p-8">
    <div class="max-w-6xl mx-auto">
      <!-- Header -->
      <div class="flex justify-between items-center mb-8">
        <div>
          <h1 class="text-3xl font-serif">My Harvest</h1>
          <p class="text-white/40 text-sm">Manage your product listings</p>
        </div>
        <button 
          @click="$emit('open-add-modal')"
          class="bg-[#2d7a18] hover:bg-[#3a9e20] text-white px-5 py-3 rounded-xl font-bold flex items-center gap-2 transition-all"
        >
          <Plus :size="18" />
          Add Product
        </button>
      </div>

      <!-- Error Message -->
      <div v-if="deleteError" class="mb-6 p-4 bg-red-500/10 border border-red-500/20 rounded-xl flex items-center gap-3">
        <AlertTriangle class="text-red-400" :size="18" />
        <span class="text-red-400 text-sm">{{ deleteError }}</span>
      </div>

      <!-- Loading State -->
      <div v-if="isLoading" class="flex justify-center py-20">
        <Loader2 class="animate-spin text-[#5cb83a]" :size="40" />
      </div>

      <!-- Empty State -->
      <div v-else-if="products.length === 0" class="text-center py-20 bg-white/2 rounded-[3rem] border border-dashed border-white/10">
        <Package class="mx-auto mb-4 text-white/10" :size="64" />
        <p class="text-white/40 text-lg mb-2">No products listed yet</p>
        <p class="text-white/20 text-sm mb-6">Add your first harvest to start selling</p>
        <button 
          @click="$emit('open-add-modal')"
          class="bg-[#2d7a18] text-white px-6 py-3 rounded-xl font-bold inline-flex items-center gap-2"
        >
          <Plus :size="18" />
          List Your First Product
        </button>
      </div>

      <!-- Products Grid -->
      <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <div 
          v-for="product in products" 
          :key="product.id"
          class="bg-[#0d2010] border border-white/10 rounded-2xl overflow-hidden hover:border-[#5cb83a]/30 transition-all"
        >
          <!-- Product Image -->
          <div class="aspect-square bg-black/30 relative">
            <img 
              :src="product.images?.[0]?.image_url || 'https://via.placeholder.com/300?text=Product'" 
              class="w-full h-full object-cover"
            />
            <div class="absolute top-3 left-3">
              <span 
                class="px-2 py-1 rounded-lg text-[8px] font-bold uppercase"
                :class="product.is_approved ? 'bg-[#5cb83a]/20 text-[#5cb83a]' : 'bg-amber-500/20 text-amber-500'"
              >
                {{ product.is_approved ? 'Active' : 'Pending' }}
              </span>
            </div>
          </div>

          <!-- Product Info -->
          <div class="p-4">
            <h3 class="font-serif text-lg mb-1">{{ product.name }}</h3>
            <p class="text-[#5cb83a] font-bold text-xl mb-3">
              ₦{{ formatCurrency(product.price) }}
              <span class="text-white/40 text-xs font-normal">/ {{ product.unit_type }}</span>
            </p>

            <div class="flex justify-between items-center text-xs text-white/40 mb-4">
              <span>{{ product.available_quantity }} available</span>
              <span>{{ product.scan_status === 'scanned' ? 'AI Verified' : 'Not Scanned' }}</span>
            </div>

            <!-- Actions -->
            <div class="flex gap-2">
              <button 
                class="flex-1 bg-white/5 hover:bg-white/10 py-2 rounded-lg text-xs font-bold uppercase flex items-center justify-center gap-1"
              >
                <Eye :size="14" /> View
              </button>
              <button 
                class="flex-1 bg-white/5 hover:bg-white/10 py-2 rounded-lg text-xs font-bold uppercase flex items-center justify-center gap-1"
              >
                <Edit :size="14" /> Edit
              </button>
              <button 
                @click="handleDelete(product.id)"
                :disabled="isDeleting === product.id"
                class="px-3 bg-red-500/10 hover:bg-red-500/20 text-red-400 rounded-lg flex items-center"
              >
                <Loader2 v-if="isDeleting === product.id" class="animate-spin" :size="14" />
                <Trash2 v-else :size="14" />
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>