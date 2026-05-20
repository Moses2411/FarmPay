<script setup>
import { computed } from 'vue';
import { Truck, MapPin, Navigation, Info } from 'lucide-vue-next';

const props = defineProps({
  productLocation: {
    type: String,
    default: ''
  },
  deliveryAddress: {
    type: Object,
    default: null
  },
  baseDeliveryFee: {
    type: Number,
    default: 2000 // Default base fee from backend
  }
});

const distanceKm = computed(() => {
  // In production, this would come from backend calculation
  // For demo, we show estimated distance
  if (!props.deliveryAddress) return null;
  
  // Mock distance based on different locations
  const locations = {
    'Kaduna': 2,
    'Zaria': 45,
    'Sabon Gari': 50,
    'Barnawa': 5,
    'GRA': 3,
    'Kafanchan': 85,
  };
  
  const city = props.deliveryAddress.city || '';
  return locations[city] || 10; // Default 10km
});

const deliveryFee = computed(() => {
  if (!distanceKm.value) return null;
  
  if (distanceKm.value <= 2) {
    return 1000; // Base fee for <= 2km
  }
  return Math.round(distanceKm.value * 1200); // N1200 per km
});

const feeBreakdown = computed(() => {
  if (!deliveryFee.value) return null;
  
  return {
    baseFee: distanceKm.value <= 2 ? 1000 : 0,
    distanceFee: distanceKm.value <= 2 ? 0 : deliveryFee.value - 1000,
    total: deliveryFee.value,
    distance: distanceKm.value
  };
});
</script>

<template>
  <div class="bg-white/5 border border-white/10 rounded-xl p-4 space-y-3">
    <div class="flex items-center gap-2 text-[#5cb83a]">
      <Truck :size="16" />
      <span class="text-[10px] uppercase font-bold tracking-wider">Delivery Fee Breakdown</span>
    </div>

    <div v-if="!deliveryAddress" class="text-center py-4">
      <MapPin class="mx-auto mb-2 text-white/20" :size="24" />
      <p class="text-xs text-white/40">Select delivery address to calculate fee</p>
    </div>

    <div v-else class="space-y-3">
      <!-- Route Info -->
      <div class="flex items-center gap-3 text-xs">
        <div class="flex flex-col items-center">
          <div class="w-2 h-2 rounded-full bg-[#5cb83a]"></div>
          <div class="w-0.5 h-8 bg-white/10"></div>
          <div class="w-2 h-2 rounded-full bg-amber-500"></div>
        </div>
        <div class="flex-1 space-y-2">
          <div class="flex justify-between">
            <span class="text-white/40">Pickup</span>
            <span class="text-white/60">{{ productLocation || 'Farm Location' }}</span>
          </div>
          <div class="flex justify-between">
            <span class="text-white/40">Delivery</span>
            <span class="text-white/60">{{ deliveryAddress.address }}, {{ deliveryAddress.city }}</span>
          </div>
        </div>
      </div>

      <!-- Distance -->
      <div class="flex justify-between items-center py-2 border-t border-b border-white/5">
        <div class="flex items-center gap-2 text-white/40">
          <Navigation :size="14" />
          <span class="text-xs">Distance</span>
        </div>
        <span class="text-sm font-medium">{{ feeBreakdown.distance }} km</span>
      </div>

      <!-- Fee Breakdown -->
      <div class="space-y-2 text-xs">
        <div v-if="feeBreakdown.baseFee > 0" class="flex justify-between text-white/50">
          <span>Base Fee (≤2km)</span>
          <span>₦{{ feeBreakdown.baseFee.toLocaleString() }}</span>
        </div>
        <div v-if="feeBreakdown.distanceFee > 0" class="flex justify-between text-white/50">
          <span>Distance Fee ({{ feeBreakdown.distance }}km × ₦1,200)</span>
          <span>₦{{ feeBreakdown.distanceFee.toLocaleString() }}</span>
        </div>
      </div>

      <!-- Total -->
      <div class="flex justify-between items-center pt-2 border-t border-white/10">
        <span class="text-[10px] uppercase font-bold text-white/60">Total Delivery Fee</span>
        <span class="text-lg font-serif text-[#5cb83a]">₦{{ feeBreakdown.total.toLocaleString() }}</span>
      </div>

      <div class="flex items-start gap-2 p-2 bg-amber-500/5 rounded-lg">
        <Info :size="14" class="text-amber-500 shrink-0 mt-0.5" />
        <p class="text-[9px] text-white/40 leading-tight">
          Fee calculated using Mapbox routing. Actual fee may vary based on route conditions.
        </p>
      </div>
    </div>
  </div>
</template>