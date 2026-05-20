<script setup>
import { ref, onMounted, onUnmounted, computed } from 'vue';
import { MapPin, Navigation, Truck, Package, CheckCircle, Clock, Loader2, RefreshCw } from 'lucide-vue-next';

const props = defineProps({
  origin: {
    type: Object,
    default: () => ({ coordinates: [7.4386, 11.0626], name: 'Kaduna Central' })
  },
  destination: {
    type: Object,
    default: null
  },
  riderLocation: {
    type: Object,
    default: null
  },
  status: {
    type: String,
    default: 'pending'
  }
});

const emit = defineEmits(['view-details']);

const mapContainer = ref(null);
const mapLoaded = ref(false);
const mapError = ref(null);

// Mock positions for demo
const mockRiderPos = ref({ lng: 7.5, lat: 11.0 });

const statusConfig = computed(() => {
  const configs = {
    pending: { color: '#6b7280', label: 'Awaiting Pickup', icon: Clock },
    assigned: { color: '#f59e0b', label: 'Assigned to Rider', icon: Package },
    in_transit: { color: '#3b82f6', label: 'In Transit', icon: Truck },
    delivered: { color: '#22c55e', label: 'Delivered', icon: CheckCircle },
    disputed: { color: '#ef4444', label: 'Issue Reported', icon: MapPin },
  };
  return configs[props.status] || configs.pending;
});

// Progress percentage for the route
const progressPercent = computed(() => {
  if (!props.destination || !props.origin) return 0;
  
  // Calculate based on status
  const statusProgress = {
    pending: 0,
    assigned: 10,
    in_transit: 50,
    delivered: 100,
    disputed: 50
  };
  
  return statusProgress[props.status] || 0;
});

// Calculate ETA (mock for demo)
const etaMinutes = computed(() => {
  if (props.status === 'delivered') return 'Arrived';
  if (props.status === 'pending' || props.status === 'assigned') return 'Awaiting';
  
  // Mock ETA calculation
  return Math.floor(Math.random() * 30) + 15;
});

const formatCoordinates = (coords) => {
  if (!coords) return 'N/A';
  const [lng, lat] = coords;
  return `${lat.toFixed(4)}°N, ${lng.toFixed(4)}°E`;
};

onMounted(() => {
  // In production, initialize Mapbox GL JS here
  // For now, we show a visual representation
  setTimeout(() => {
    mapLoaded.value = true;
  }, 500);
});
</script>

<template>
  <div class="bg-[#0d2010] border border-white/10 rounded-2xl overflow-hidden">
    <!-- Map Header -->
    <div class="p-4 border-b border-white/5 flex justify-between items-center">
      <div class="flex items-center gap-3">
        <div class="p-2 rounded-xl" :style="{ backgroundColor: statusConfig.color + '20' }">
          <component :is="statusConfig.icon" :size="20" :style="{ color: statusConfig.color }" />
        </div>
        <div>
          <p class="text-xs font-bold text-white">{{ statusConfig.label }}</p>
          <p class="text-[10px] text-white/40">Live Tracking</p>
        </div>
      </div>
      
      <button 
        @click="$emit('view-details')"
        class="text-[#5cb83a] text-xs font-bold uppercase hover:underline"
      >
        View Details
      </button>
    </div>

    <!-- Map Visual (Demo - would use Mapbox in production) -->
    <div class="relative h-64 bg-black/40 overflow-hidden">
      <!-- Grid Background -->
      <div class="absolute inset-0 opacity-20" 
           style="background-image: radial-gradient(circle, #5cb83a 1px, transparent 1px); background-size: 20px 20px;">
      </div>

      <!-- Route Line -->
      <svg class="absolute inset-0 w-full h-full" viewBox="0 0 100 100" preserveAspectRatio="none">
        <defs>
          <linearGradient id="routeGradient" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" :style="{ stopColor: '#5cb83a', stopOpacity: 0.3 }" />
            <stop :offset="progressPercent" :style="{ stopColor: '#5cb83a', stopOpacity: 1 }" />
            <stop :offset="progressPercent" :style="{ stopColor: '#3b82f6', stopOpacity: 1 }" />
            <stop offset="100%" :style="{ stopColor: '#3b82f6', stopOpacity: 0.3 }" />
          </linearGradient>
        </defs>
        <!-- Route path -->
        <path d="M 15,80 Q 30,60 50,50 T 85,20" 
              fill="none" 
              stroke="url(#routeGradient)" 
              stroke-width="2"
              stroke-linecap="round"/>
      </svg>

      <!-- Origin Marker -->
      <div class="absolute left-[15%] top-[80%] transform -translate-x-1/2 -translate-y-1/2">
        <div class="w-8 h-8 bg-[#5cb83a] rounded-full flex items-center justify-center shadow-lg shadow-[#5cb83a]/30">
          <MapPin :size="14" class="text-black" />
        </div>
        <p class="text-[8px] text-white/60 text-center mt-1">Farm</p>
      </div>

      <!-- Destination Marker -->
      <div class="absolute left-[85%] top-[20%] transform -translate-x-1/2 -translate-y-1/2">
        <div class="w-8 h-8 bg-amber-500 rounded-full flex items-center justify-center shadow-lg shadow-amber-500/30">
          <Navigation :size="14" class="text-black" />
        </div>
        <p class="text-[8px] text-white/60 text-center mt-1">Buyer</p>
      </div>

      <!-- Rider Marker (animated) -->
      <div 
        v-if="riderLocation || status === 'in_transit'"
        class="absolute left-[50%] top-[50%] transform -translate-x-1/2 -translate-y-1/2 transition-all duration-1000"
        :style="{ left: `${15 + (progressPercent * 0.7)}%`, top: `${80 - (progressPercent * 0.6)}%` }"
      >
        <div class="relative">
          <div class="w-10 h-10 bg-blue-500 rounded-full flex items-center justify-center shadow-lg shadow-blue-500/50 animate-pulse">
            <Truck :size="18" class="text-white" />
          </div>
          <div class="absolute -bottom-1 left-1/2 -translate-x-1/2 w-2 h-2 bg-blue-400 rounded-full animate-ping"></div>
        </div>
      </div>

      <!-- Loading State -->
      <div v-if="!mapLoaded" class="absolute inset-0 flex items-center justify-center bg-black/60">
        <div class="text-center">
          <Loader2 class="animate-spin text-[#5cb83a] mx-auto mb-2" :size="24" />
          <p class="text-[10px] text-white/40">Loading map...</p>
        </div>
      </div>
    </div>

    <!-- Status Timeline -->
    <div class="p-4 border-t border-white/5">
      <div class="flex items-center justify-between">
        <div class="flex items-center gap-2">
          <Clock :size="14" class="text-white/40" />
          <span class="text-xs text-white/60">ETA: <span class="text-white font-bold">{{ etaMinutes }}</span></span>
        </div>
        <div class="flex items-center gap-1">
          <span class="text-[10px] text-white/40 uppercase">Progress</span>
          <span class="text-sm font-bold text-[#5cb83a]">{{ progressPercent }}%</span>
        </div>
      </div>

      <!-- Progress Bar -->
      <div class="mt-3 h-1.5 bg-white/10 rounded-full overflow-hidden">
        <div 
          class="h-full rounded-full transition-all duration-500"
          :style="{ 
            width: `${progressPercent}%`,
            backgroundColor: status === 'disputed' ? '#ef4444' : '#5cb83a'
          }"
        ></div>
      </div>

      <!-- Coordinates Info -->
      <div class="mt-4 grid grid-cols-2 gap-3 text-[10px]">
        <div class="bg-white/5 rounded-lg p-2">
          <p class="text-white/30 uppercase mb-1">Pickup</p>
          <p class="text-white/60 font-mono">{{ formatCoordinates(origin?.coordinates) }}</p>
        </div>
        <div class="bg-white/5 rounded-lg p-2">
          <p class="text-white/30 uppercase mb-1">Delivery</p>
          <p class="text-white/60 font-mono">{{ formatCoordinates(destination?.coordinates) }}</p>
        </div>
      </div>
    </div>
  </div>
</template>