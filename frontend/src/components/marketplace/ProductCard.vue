<script setup>
import { ShieldCheck, MapPin, ShoppingCart, Info } from 'lucide-vue-next';
import { computed } from 'vue';

const props = defineProps({
  product: {
    type: Object,
    required: true
  }
});
console.log(props.product)

const productImageUrl = computed(() => {
  const baseUrl = import.meta.env.VITE_BASE_API_URL || 'https://farmpay-j8a4.onrender.com';
  const relativePath = props.product?.images?.[0]?.image_url || '';
  return `${baseUrl}${relativePath}`;
});

console.log(productImageUrl)
// We define the emit so the parent Marketplace.vue knows when to open the modal
defineEmits(['open-modal']);

console.log(props.product.images[0].image_url)
</script>

<template>
  <div class="bg-white/5 border border-white/10 rounded-3xl overflow-hidden group hover:border-[#5cb83a]/50 transition-all duration-300">
    <div class="relative aspect-square overflow-hidden">
      <img :src="productImageUrl" @error="(e) => e.target.src = 'https://via.placeholder.com/400?text=FarmPay+Produce'"
           class="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500" />
      
      <div class="absolute top-4 left-4 bg-[#061209]/80 backdrop-blur-md border border-[#5cb83a]/30 px-3 py-1.5 rounded-full flex items-center gap-2">
        <ShieldCheck class="text-[#5cb83a]" :size="14" />
        <span class="text-[10px] font-bold text-white uppercase tracking-wider"> {{ product.images[0].scan_result.disease_detected ?  "NOT VERIFIED" :"AI VERIFIED"}}</span>
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
        <span class="italic text-[10px]">{{ product.farmer_name }}</span>
      </div>

      <button 
        @click="$emit('open-modal', product)"
        class="w-full bg-[#2d7a18] hover:bg-[#3a9e20] text-white py-3 rounded-xl font-bold flex items-center justify-center gap-2 transition-all mt-2 active:scale-95 shadow-lg shadow-[#2d7a18]/20"
      >
        <ShoppingCart :size="18" />
        Pay to Escrow
      </button>
    </div>
  </div>
</template>