<script setup>
import { ref, watch } from 'vue';
import { MapPin, Search, Loader2, X, Navigation } from 'lucide-vue-next';
import { useMapbox } from '@/composables/useMapbox';

const emit = defineEmits(['select', 'update:modelValue']);

const props = defineProps({
  modelValue: {
    type: Object,
    default: null
  },
  placeholder: {
    type: String,
    default: 'Enter delivery address...'
  },
  label: {
    type: String,
    default: 'Delivery Address'
  }
});

const { 
  isLoading, 
  searchResults, 
  selectedLocation, 
  hasToken,
  searchAddress, 
  selectLocation, 
  clearSelection 
} = useMapbox();

const searchQuery = ref('');
const showDropdown = ref(false);

let debounceTimer = null;

const handleInput = () => {
  showDropdown.value = true;
  clearTimeout(debounceTimer);
  debounceTimer = setTimeout(() => {
    searchAddress(searchQuery.value);
  }, 300);
};

const handleSelect = (location) => {
  selectLocation(location);
  searchQuery.value = location.address;
  showDropdown.value = false;
  emit('select', location);
  emit('update:modelValue', location);
};

const handleClear = () => {
  searchQuery.value = '';
  clearSelection();
  emit('select', null);
  emit('update:modelValue', null);
};

const formatAddress = (location) => {
  if (!location) return '';
  return location.city ? `${location.address}, ${location.city}` : location.address;
};
</script>

<template>
  <div class="relative">
    <label class="text-[10px] uppercase font-bold text-white/40 tracking-widest block mb-2">
      {{ label }}
      <span v-if="!hasToken" class="text-amber-500/60 normal-case text-[8px] ml-2">(Demo Mode)</span>
    </label>

    <div class="relative">
      <MapPin class="absolute left-4 top-1/2 -translate-y-1/2 text-white/30" :size="18" />
      
      <input 
        v-model="searchQuery"
        @input="handleInput"
        @focus="showDropdown = true"
        type="text"
        :placeholder="placeholder"
        class="w-full bg-white/5 border border-white/10 rounded-xl py-4 pl-12 pr-12 text-sm outline-none focus:border-[#5cb83a] transition-all"
      />

      <button 
        v-if="searchQuery" 
        @click="handleClear"
        class="absolute right-4 top-1/2 -translate-y-1/2 text-white/30 hover:text-white"
      >
        <X :size="16" />
      </button>

      <div v-if="isLoading" class="absolute right-12 top-1/2 -translate-y-1/2">
        <Loader2 class="animate-spin text-[#5cb83a]" :size="16" />
      </div>
    </div>

    <!-- Search Results Dropdown -->
    <div 
      v-if="showDropdown && searchResults.length > 0"
      class="absolute z-50 w-full mt-2 bg-[#0d2010] border border-white/10 rounded-xl overflow-hidden shadow-2xl max-h-60 overflow-y-auto"
    >
      <button
        v-for="result in searchResults"
        :key="result.id || result.address"
        @click="handleSelect(result)"
        class="w-full px-4 py-3 text-left hover:bg-white/5 border-b border-white/5 last:border-0 transition-colors"
      >
        <div class="flex items-start gap-3">
          <MapPin class="text-[#5cb83a] shrink-0 mt-0.5" :size="14" />
          <div>
            <p class="text-sm font-medium text-white">{{ result.address }}</p>
            <p class="text-[10px] text-white/40">{{ result.city }}{{ result.state ? `, ${result.state}` : '' }}</p>
          </div>
        </div>
      </button>
    </div>

    <!-- No Results -->
    <div 
      v-if="showDropdown && searchQuery && searchResults.length === 0 && !isLoading"
      class="absolute z-50 w-full mt-2 bg-[#0d2010] border border-white/10 rounded-xl p-4 text-center"
    >
      <p class="text-xs text-white/40">No addresses found. Try a different search.</p>
    </div>

    <!-- Selected Location Display -->
    <div v-if="selectedLocation && !searchQuery" class="mt-3 p-3 bg-[#5cb83a]/10 border border-[#5cb83a]/20 rounded-xl flex items-center gap-3">
      <Navigation class="text-[#5cb83a]" :size="16" />
      <div>
        <p class="text-xs text-[#5cb83a] font-bold uppercase">Selected Location</p>
        <p class="text-sm text-white/80">{{ formatAddress(selectedLocation) }}</p>
      </div>
    </div>
  </div>
</template>

<style scoped>
.max-h-60 {
  max-height: 15rem;
}
</style>