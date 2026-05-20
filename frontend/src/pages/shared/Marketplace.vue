<script setup>
import { ref, onMounted } from 'vue';
import api from '@/api/api';
import ProductCard from '@/components/marketplace/ProductCard.vue';
import PaymentModal from '@/components/PaymentModal.vue';
import { Search, Loader2, Package } from 'lucide-vue-next';

const products = ref([]);
const loading = ref(true);
const isModalOpen = ref(false);
const selectedProduct = ref(null);

// 1. Fetch live products from backend
const fetchProducts = async () => {
  loading.value = true;
  try {
    // Calling your products endpoint
    const response = await api.get('/products/all');
    
    // Check if we actually got an array back
    if (Array.isArray(response)) {
      products.value = response;
    } else {
      console.warn("Unexpected data format from backend:", response.data);
    }
  } catch (err) {
    console.error("Backend fetch failed, showing mock data for preview:", err);
    // Keep mock data only as a fallback for your demo/judges
    products.value = mockProducts;
  } finally {
    loading.value = false;
  }
};

const openPaymentModal = (product) => {
  selectedProduct.value = product;
  isModalOpen.value = true;
};

const handlePayment = async () => {
  console.log("Processing escrow for:", selectedProduct.value.name);
  // Ideally, your PaymentModal emits a 'confirm' that hits an 
  // /orders/create endpoint before closing
  isModalOpen.value = false;
};

// Keep mockProducts here as the fallback you defined
const mockProducts = [
  {
    id: "550e8400-e29b-41d4-a716-446655440000",
    name: "Zaria Plum Tomatoes",
    price: 15500,
    unit_type: "Basket",
    location: "Zaria (Zone 1)",
    quality_score: 98,
    images: [{ image_url: "https://images.unsplash.com/photo-1582284540020-8acbe03f4924?auto=format&fit=crop&w=400&q=80" }],
    farmer_name: "Amina Yusuf"
  },
  {
    id: "550e8400-e29b-41d4-a716-446655440001",
    name: "Fresh Pepper Mix",
    price: 8500,
    unit_type: "Basket",
    location: "Kaduna (Zone 2)",
    quality_score: 95,
    images: [{ image_url: "https://images.unsplash.com/photo-1582284540020-8acbe03f4924?auto=format&fit=crop&w=400&q=80" }],
    farmer_name: "Garba Abubakar"
  },
  {
    id: "550e8400-e29b-41d4-a716-446655440002",
    name: "Green Maize",
    price: 12000,
    unit_type: "100kg Bag",
    location: "Zaria (Zone 1)",
    quality_score: 92,
    images: [{ image_url: "https://images.unsplash.com/photo-1582284540020-8acbe03f4924?auto=format&fit=crop&w=400&q=80" }],
    farmer_name: "Fatima Bello"
  }
];

onMounted(fetchProducts);
</script>

<template>
  <div class="min-h-screen bg-[#061209] text-[#f0ede4] py-8 px-4 md:px-8 lg:px-12 font-sans">
    <div class="w-full mx-auto"> 
      
      <header class="mb-12 flex flex-col md:flex-row md:items-end justify-between gap-6">
        <div>
          <h1 class="text-4xl md:text-5xl font-serif mb-2 text-[#f0ede4]">Kaduna Produce Market</h1>
          <p class="text-white/40 italic text-sm">Direct from farm to your doorstep. Verified by AI.</p>
        </div>
        
        <div class="flex gap-3">
          <div class="relative group">
            <Search class="absolute left-4 top-1/2 -translate-y-1/2 text-white/20 group-focus-within:text-[#5cb83a] transition-colors" :size="18" />
            <input 
              type="text" 
              placeholder="Search produce..." 
              class="bg-white/5 border border-white/10 rounded-xl py-4 pl-12 pr-4 focus:border-[#5cb83a] focus:bg-white/8 outline-none w-full md:w-80 transition-all text-sm" 
            />
          </div>
        </div>
      </header>

      <div v-if="loading" class="flex flex-col items-center justify-center py-32 border border-white/5 rounded-[3rem] bg-white/2">
        <Loader2 class="animate-spin text-[#5cb83a] mb-4" :size="48" />
        <p class="animate-pulse text-white/40 uppercase tracking-widest text-[10px] font-bold">Scanning the harvest...</p>
      </div>

      <div v-else-if="products.length > 0" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 2xl:grid-cols-5 gap-6 lg:gap-8">
        <ProductCard 
          v-for="p in products" 
          :key="p.id" 
          :product="p" 
          @open-modal="openPaymentModal"
        />
      </div>

      <div v-else class="text-center py-32 border border-dashed border-white/10 rounded-[3rem] bg-white/2">
        <Package class="mx-auto mb-4 text-white/10" :size="48" />
        <p class="text-white/20 italic">No produce listed in your area yet.</p>
        <button @click="fetchProducts" class="mt-4 text-[#5cb83a] text-xs font-bold uppercase tracking-widest hover:underline">
          Retry Fetch
        </button>
      </div>

      <PaymentModal 
        v-if="selectedProduct"
        :is-open="isModalOpen" 
        :product="selectedProduct" 
        @close="isModalOpen = false"
        @confirm="handlePayment" 
      />
    </div>
  </div>
</template>