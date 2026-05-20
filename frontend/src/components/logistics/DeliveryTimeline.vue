<script setup>
import { computed } from 'vue';
import { CheckCircle, Circle, Clock, MapPin, Package, Truck, Navigation, AlertTriangle } from 'lucide-vue-next';

const props = defineProps({
  events: {
    type: Array,
    default: () => []
  },
  currentStatus: {
    type: String,
    default: 'pending'
  }
});

const timelineEvents = computed(() => {
  const allEvents = [
    { key: 'created', label: 'Order Created', icon: Package, defaultDesc: 'Order placed and payment confirmed' },
    { key: 'assigned', label: 'Rider Assigned', icon: Truck, defaultDesc: 'Dispatch rider assigned to delivery' },
    { key: 'picked_up', label: 'Picked Up', icon: MapPin, defaultDesc: 'Package collected from farmer' },
    { key: 'in_transit', label: 'In Transit', icon: Truck, defaultDesc: 'On the way to delivery location' },
    { key: 'delivered', label: 'Delivered', icon: CheckCircle, defaultDesc: 'Package delivered successfully' },
    { key: 'completed', label: 'Completed', icon: CheckCircle, defaultDesc: 'OTP verified, payment released' },
  ];

  const statusIndex = {
    'pending': 0,
    'assigned': 1,
    'picked-up': 2,
    'in_transit': 3,
    'delivered': 4,
    'completed': 5,
  };

  const currentIndex = statusIndex[props.currentStatus] ?? 0;

  return allEvents.map((event, index) => {
    // Find matching event from props.events or create default
    const matchedEvent = props.events.find(e => 
      e.status?.toLowerCase().includes(event.key) || 
      e.type?.toLowerCase() === event.key
    );

    const isCompleted = index <= currentIndex;
    const isCurrent = index === currentIndex;

    return {
      ...event,
      completed: isCompleted,
      current: isCurrent,
      timestamp: matchedEvent?.timestamp || null,
      description: matchedEvent?.description || event.defaultDesc,
      location: matchedEvent?.location || null,
    };
  });
});

const formatTime = (timestamp) => {
  if (!timestamp) return '';
  const date = new Date(timestamp);
  return date.toLocaleString('en-GB', { 
    day: '2-digit', 
    month: 'short', 
    hour: '2-digit', 
    minute: '2-digit' 
  });
};
</script>

<template>
  <div class="bg-[#0d2010] border border-white/10 rounded-2xl p-5">
    <h3 class="text-sm font-bold text-white mb-5 flex items-center gap-2">
      <Clock :size="16" class="text-[#5cb83a]" />
      Delivery Timeline
    </h3>

    <div class="relative">
      <!-- Vertical Line -->
      <div class="absolute left-[15px] top-0 bottom-0 w-0.5 bg-white/10"></div>

      <div class="space-y-5">
        <div 
          v-for="(event, index) in timelineEvents" 
          :key="event.key"
          class="relative flex gap-4"
        >
          <!-- Icon -->
          <div 
            class="relative z-10 w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 transition-all"
            :class="{
              'bg-[#5cb83a] text-black': event.completed && !event.current,
              'bg-blue-500 text-white ring-4 ring-blue-500/30': event.current,
              'bg-white/10 text-white/20': !event.completed && !event.current,
            }"
          >
            <component 
              :is="event.completed ? CheckCircle : event.current ? Circle : event.icon" 
              :size="event.current ? 20 : 14" 
              :class="event.current ? 'animate-pulse' : ''"
            />
          </div>

          <!-- Content -->
          <div class="flex-1 pb-6">
            <div class="flex items-center justify-between">
              <span 
                class="text-sm font-bold"
                :class="event.current ? 'text-blue-400' : event.completed ? 'text-white' : 'text-white/40'"
              >
                {{ event.label }}
              </span>
              <span v-if="event.timestamp" class="text-[10px] text-white/30">
                {{ formatTime(event.timestamp) }}
              </span>
            </div>

            <p class="text-xs text-white/50 mt-1">{{ event.description }}</p>

            <div v-if="event.location" class="mt-2 flex items-center gap-1 text-[10px] text-[#5cb83a]">
              <MapPin :size="10" />
              <span>{{ event.location }}</span>
            </div>

            <!-- Current Status Indicator -->
            <div 
              v-if="event.current"
              class="mt-2 inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-blue-500/10 border border-blue-500/20"
            >
              <span class="w-1.5 h-1.5 bg-blue-500 rounded-full animate-pulse"></span>
              <span class="text-[10px] font-bold text-blue-400 uppercase">In Progress</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Issue Reporting -->
    <div class="mt-6 pt-4 border-t border-white/5">
      <button class="flex items-center gap-2 text-xs text-red-400 hover:text-red-300 transition-colors">
        <AlertTriangle :size="14" />
        <span>Report an issue with this delivery</span>
      </button>
    </div>
  </div>
</template>