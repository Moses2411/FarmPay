<script setup>
import { ref } from 'vue';
import { ShieldCheck, MapPin, ShoppingCart, Star, Eye } from 'lucide-vue-next';
import { getProductReviews } from '@/api/api';
import Reviews from './Reviews.vue';

const props = defineProps({
  product: {
    type: Object,
    required: true
  }
});

const emit = defineEmits(['open-modal']);

const showReviews = ref(false);
const showDetail = ref(false);
const reviewCount = ref(0);

const loadReviewCount = async () => {
  try {
    const reviews = await getProductReviews(props.product.id);
    reviewCount.value = (reviews.length || 0);
  } catch (err) {
    console.error("Failed to load reviews:", err);
  }
};

const openReviews = async () => {
  showReviews.value = true;
  await loadReviewCount();
};
</script>

<template>
  <div class="bg-white/5 border border-white/10 rounded-3xl overflow-hidden group hover:border-[#5cb83a]/50 transition-all duration-300 relative">
    <div class="relative aspect-square overflow-hidden">
      <img :src="product?.images?.[0]?.image_url || 'https://via.placeholder.com/400?text=FarmPay+Produce'" @error="(e) => e.target.src = 'https://via.placeholder.com/400?text=FarmPay+Produce'"
           class="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500" />
      
      <div class="absolute top-4 left-4 bg-[#061209]/80 backdrop-blur-md border border-[#5cb83a]/30 px-3 py-1.5 rounded-full flex items-center gap-2">
        <ShieldCheck class="text-[#5cb83a]" :size="14" />
        <span class="text-[10px] font-bold text-white uppercase tracking-wider">
          AI VERIFIED
        </span>
      </div>

      <div class="absolute bottom-4 right-4 bg-white/10 backdrop-blur-md border border-white/10 px-3 py-1 rounded-lg">
        <span class="text-[10px] font-bold text-white/70 uppercase tracking-widest">Per {{ product.unit_type || 'Unit' }}</span>
      </div>
    </div>

    <div class="p-5 space-y-3">
      <div class="flex justify-between items-start gap-2">
        <h3 class="font-serif text-lg leading-tight flex-1">{{ product.name }}</h3>
        <div class="text-right">
          <span class="text-[#5cb83a] font-bold text-lg block">₦{{ product.price.toLocaleString() }}</span>
        </div>
      </div>

      <div class="flex items-center justify-between text-white/40 text-xs">
        <div class="flex items-center gap-2">
          <MapPin :size="14" />
          <span>{{ product.location || 'Zaria, Zone 1' }}</span>
        </div>
        <span class="italic text-[10px]">{{ product.farmer?.user?.full_name || product.farmer_name }}</span>
      </div>

      <div class="flex items-center gap-3 pt-2">
        <button 
          @click="openReviews"
          class="flex items-center gap-1.5 text-[10px] text-white/40 hover:text-[#5cb83a] transition-colors"
        >
          <Star :size="14" class="text-amber-400 fill-amber-400" />
          <span>Reviews</span>
        </button>
        <button 
          @click="showDetail = true"
          class="flex items-center gap-1.5 text-[10px] text-white/40 hover:text-white transition-colors"
        >
          <Eye :size="14" />
          <span>Details</span>
        </button>
      </div>

      <div class="flex gap-2 mt-2">
        <button 
          @click="showDetail = true"
          class="flex-1 bg-white/5 hover:bg-white/10 text-white py-2 rounded-xl font-bold text-xs uppercase flex items-center justify-center gap-1 transition-all"
        >
          <Eye :size="14" />
          View
        </button>
        <button 
          @click="$emit('open-modal', product)"
          class="flex-[2] bg-[#2d7a18] hover:bg-[#3a9e20] text-white py-2 rounded-xl font-bold flex items-center justify-center gap-2 transition-all active:scale-95 shadow-lg shadow-[#2d7a18]/20"
        >
          <ShoppingCart :size="16" />
          Buy
        </button>
      </div>
    </div>

    <!-- Reviews Modal -->
    <div v-if="showReviews" class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-[#061209]/95 backdrop-blur-md">
      <div class="w-full max-w-lg">
        <button 
          @click="showReviews = false" 
          class="absolute top-6 right-6 text-white/40 hover:text-white"
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
        </button>
        <Reviews :productId="product.id" @close="showReviews = false" />
      </div>
    </div>
  </div>
</template>