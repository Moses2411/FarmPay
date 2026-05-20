<script setup>
import { computed } from 'vue';
import { X, MapPin, ShieldCheck, AlertTriangle, CheckCircle, User, ShoppingCart } from 'lucide-vue-next';

const props = defineProps({
  product: {
    type: Object,
    required: true
  },
  isOpen: {
    type: Boolean,
    default: false
  }
});

const emit = defineEmits(['close', 'buy']);

const isHealthy = computed(() => {
  const scanResult = props.product?.images?.[0]?.scan_result;
  return !scanResult?.disease_detected;
});

const diseaseInfo = computed(() => {
  const scanResult = props.product?.images?.[0]?.scan_result;
  if (scanResult?.disease_detected) {
    return {
      name: scanResult.disease_name || 'Unknown Issue',
      status: scanResult.status
    };
  }
  return null;
});

const farmerInfo = computed(() => {
  return props.product?.farmer || {};
});

const formatCurrency = (value) => {
  return new Intl.NumberFormat('en-NG', { style: 'currency', currency: 'NGN', minimumFractionDigits: 0 }).format(value);
};
</script>

<template>
  <div v-if="isOpen" class="fixed inset-0 z-60 flex items-center justify-center p-4 bg-[#061209]/95 backdrop-blur-md">
    <div class="bg-[#0d2010] border border-white/10 w-full max-w-2xl rounded-[3rem] p-8 relative shadow-2xl max-h-[90vh] overflow-y-auto">
      
      <button @click="$emit('close')" class="absolute top-6 right-6 text-white/20 hover:text-white">
        <X :size="24" />
      </button>

      <!-- Product Image -->
      <div class="relative h-64 rounded-2xl overflow-hidden mb-6">
        <img 
          :src="product?.images?.[0]?.image_url || 'https://via.placeholder.com/400'" 
          class="w-full h-full object-cover"
        />
        
        <!-- Health Badge -->
        <div class="absolute top-4 left-4">
          <span 
            class="px-4 py-2 rounded-full text-xs font-bold uppercase flex items-center gap-2"
            :class="isHealthy ? 'bg-[#5cb83a]/90 text-black' : 'bg-red-500/90 text-white'"
          >
            <component :is="isHealthy ? CheckCircle : AlertTriangle" :size="14" />
            {{ isHealthy ? 'AI Verified - Healthy' : 'Health Warning' }}
          </span>
        </div>
      </div>

      <!-- Unhealthy Warning Banner -->
      <div v-if="!isHealthy" class="mb-6 p-4 bg-red-500/10 border border-red-500/20 rounded-2xl">
        <div class="flex items-start gap-3">
          <AlertTriangle class="text-red-400 shrink-0 mt-0.5" :size="24" />
          <div>
            <p class="font-bold text-red-400">Issue Detected: {{ diseaseInfo?.name }}</p>
            <p class="text-sm text-white/60 mt-1">
              This product has been flagged due to quality concerns. Review the details below before proceeding.
            </p>
          </div>
        </div>
      </div>

      <!-- Product Info -->
      <div class="mb-6">
        <h2 class="text-2xl font-serif text-white mb-2">{{ product?.name }}</h2>
        <p class="text-white/60">{{ product?.description || 'No description provided' }}</p>
      </div>

      <!-- Price & Details Grid -->
      <div class="grid grid-cols-2 gap-4 mb-6">
        <div class="bg-white/5 p-4 rounded-xl">
          <p class="text-[10px] text-white/40 uppercase mb-1">Price</p>
          <p class="text-2xl font-serif text-[#5cb83a]">{{ formatCurrency(product?.price) }}</p>
          <p class="text-xs text-white/40">per {{ product?.unit_type || 'unit' }}</p>
        </div>
        <div class="bg-white/5 p-4 rounded-xl">
          <p class="text-[10px] text-white/40 uppercase mb-1">Available</p>
          <p class="text-xl font-serif text-white">{{ product?.available_quantity }}</p>
          <p class="text-xs text-white/40">units in stock</p>
        </div>
      </div>

      <!-- Location -->
      <div class="flex items-center gap-2 text-white/50 mb-6">
        <MapPin :size="16" />
        <span>{{ product?.location || 'Kaduna, Nigeria' }}</span>
      </div>

      <!-- Farmer Info -->
      <div class="p-4 bg-white/5 rounded-xl mb-6">
        <p class="text-[10px] text-white/40 uppercase mb-3">Seller Information</p>
        <div class="flex items-center gap-3">
          <div class="w-10 h-10 bg-[#5cb83a]/20 rounded-full flex items-center justify-center">
            <User :size="18" class="text-[#5cb83a]" />
          </div>
          <div>
            <p class="font-medium text-white">{{ farmerInfo?.user?.full_name || farmerInfo?.business_name || 'Farmer' }}</p>
            <p class="text-xs text-white/40">Verified Farmer</p>
          </div>
        </div>
      </div>

      <!-- Quality Info -->
      <div class="p-4 bg-white/5 rounded-xl mb-6">
        <p class="text-[10px] text-white/40 uppercase mb-3">Quality Verification</p>
        <div class="flex items-center gap-2">
          <ShieldCheck :size="18" class="text-[#5cb83a]" />
          <span class="text-sm text-white/80">AI Quality Scan Completed</span>
        </div>
        <p v-if="isHealthy" class="text-xs text-[#5cb83a] mt-2">
          ✓ Product passed quality verification - safe for consumption
        </p>
        <p v-else class="text-xs text-red-400 mt-2">
          ⚠ Quality scan detected issues - buyer discretion advised
        </p>
      </div>

      <!-- Action Buttons -->
      <div class="flex gap-4">
        <button 
          @click="$emit('close')"
          class="flex-1 bg-white/5 text-white py-4 rounded-xl font-bold text-sm uppercase hover:bg-white/10 transition-all"
        >
          Cancel
        </button>
        <button 
          @click="$emit('buy', product)"
          class="flex-1 bg-[#2d7a18] text-white py-4 rounded-xl font-bold text-sm uppercase flex items-center justify-center gap-2 hover:bg-[#3a9e20] transition-all"
        >
          <ShoppingCart :size="18" />
          Proceed to Buy
        </button>
      </div>

      <!-- Disclaimer for unhealthy products -->
      <p v-if="!isHealthy" class="text-[10px] text-white/30 text-center mt-4">
        By purchasing this product, you acknowledge the quality warning above.
      </p>
    </div>
  </div>
</template>