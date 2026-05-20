<script setup>
import { ref, computed, onMounted } from 'vue';
import { Cloud, Sun, CloudRain, Wind, Droplets, Thermometer, AlertTriangle, Loader2 } from 'lucide-vue-next';

const props = defineProps({
  location: {
    type: String,
    default: 'Kaduna'
  }
});

const isLoading = ref(true);
const weatherData = ref(null);
const forecast = ref([]);

// Mock weather data for demo
const mockWeather = {
  current: {
    temp: 28,
    condition: 'partly_cloudy',
    humidity: 65,
    windSpeed: 12,
    description: 'Partly Cloudy',
    icon: 'partly-cloudy'
  },
  alerts: [
    { type: 'rain', message: 'Heavy rain expected tomorrow', severity: 'warning' }
  ]
};

const mockForecast = [
  { day: 'Today', high: 32, low: 24, condition: 'partly_cloudy', rain: 10 },
  { day: 'Tomorrow', high: 30, low: 23, condition: 'rainy', rain: 70 },
  { day: 'Wed', high: 31, low: 24, condition: 'cloudy', rain: 30 },
  { day: 'Thu', high: 33, low: 25, condition: 'sunny', rain: 5 },
  { day: 'Fri', high: 32, low: 24, condition: 'sunny', rain: 0 },
];

const getWeatherIcon = (condition) => {
  const icons = {
    'sunny': Sun,
    'cloudy': Cloud,
    'partly_cloudy': Cloud,
    'rainy': CloudRain,
    'stormy': CloudRain,
  };
  return icons[condition] || Cloud;
};

const getWeatherColor = (condition) => {
  const colors = {
    'sunny': 'text-amber-400',
    'cloudy': 'text-white/40',
    'partly_cloudy': 'text-white/60',
    'rainy': 'text-blue-400',
    'stormy': 'text-blue-600',
  };
  return colors[condition] || 'text-white/60';
};

onMounted(() => {
  // Simulate API call
  setTimeout(() => {
    weatherData.value = mockWeather.current;
    forecast.value = mockForecast;
    isLoading.value = false;
  }, 500);
});
</script>

<template>
  <div class="bg-[#0d2010] border border-white/10 rounded-2xl overflow-hidden">
    <!-- Current Weather Header -->
    <div class="p-5 border-b border-white/5">
      <div class="flex items-center justify-between">
        <div>
          <p class="text-[10px] text-white/40 uppercase tracking-wider">Current Weather</p>
          <p class="text-xs text-white/60 mt-1">{{ location }}</p>
        </div>
        <div v-if="weatherData" class="flex items-center gap-2">
          <component :is="getWeatherIcon(weatherData.condition)" :size="32" :class="getWeatherColor(weatherData.condition)" />
          <span class="text-3xl font-serif text-white">{{ weatherData.temp }}°</span>
        </div>
      </div>

      <p v-if="weatherData" class="text-sm text-white/60 mt-2">{{ weatherData.description }}</p>
      
      <!-- Loading State -->
      <div v-if="isLoading" class="flex items-center justify-center py-4">
        <Loader2 class="animate-spin text-[#5cb83a]" :size="24" />
      </div>
    </div>

    <!-- Weather Details Grid -->
    <div v-if="weatherData" class="p-5 grid grid-cols-3 gap-4 border-b border-white/5">
      <div class="text-center">
        <div class="p-2 bg-blue-500/10 rounded-xl inline-flex mb-2">
          <Droplets :size="18" class="text-blue-400" />
        </div>
        <p class="text-lg font-serif text-white">{{ weatherData.humidity }}%</p>
        <p class="text-[8px] text-white/40 uppercase">Humidity</p>
      </div>
      <div class="text-center">
        <div class="p-2 bg-white/10 rounded-xl inline-flex mb-2">
          <Wind :size="18" class="text-white/60" />
        </div>
        <p class="text-lg font-serif text-white">{{ weatherData.windSpeed }} <span class="text-xs">km/h</span></p>
        <p class="text-[8px] text-white/40 uppercase">Wind</p>
      </div>
      <div class="text-center">
        <div class="p-2 bg-amber-500/10 rounded-xl inline-flex mb-2">
          <Thermometer :size="18" class="text-amber-400" />
        </div>
        <p class="text-lg font-serif text-white">UV 6</p>
        <p class="text-[8px] text-white/40 uppercase">UV Index</p>
      </div>
    </div>

    <!-- Alerts Section -->
    <div v-if="weatherData?.alerts?.length > 0" class="p-4 bg-amber-500/10 border-b border-amber-500/20">
      <div class="flex items-start gap-3">
        <AlertTriangle :size="16" class="text-amber-400 shrink-0 mt-0.5" />
        <div>
          <p class="text-xs text-amber-400 font-bold">Weather Alert</p>
          <p class="text-[10px] text-white/60 mt-1">{{ weatherData.alerts[0].message }}</p>
        </div>
      </div>
    </div>

    <!-- 5-Day Forecast -->
    <div class="p-5">
      <h4 class="text-[10px] text-white/40 uppercase font-bold tracking-wider mb-4">5-Day Forecast</h4>
      
      <div class="space-y-3">
        <div 
          v-for="day in forecast" 
          :key="day.day"
          class="flex items-center justify-between"
        >
          <span class="text-xs text-white/60 w-20">{{ day.day }}</span>
          
          <component :is="getWeatherIcon(day.condition)" :size="16" :class="getWeatherColor(day.condition)" />
          
          <div class="flex items-center gap-2 w-24 justify-end">
            <span v-if="day.rain > 20" class="flex items-center gap-1 text-[10px] text-blue-400">
              <Droplets :size="10" /> {{ day.rain }}%
            </span>
          </div>
          
          <div class="flex items-center gap-1 w-20 justify-end">
            <span class="text-xs text-white/40">{{ day.low }}°</span>
            <div class="w-12 h-1.5 bg-white/10 rounded-full mx-1 overflow-hidden">
              <div 
                class="h-full bg-gradient-to-r from-blue-400 to-amber-400 rounded-full"
                :style="{ width: `${((day.high - day.low) / 20) * 100}%`, marginLeft: `${((day.low - 20) / 15) * 100}%` }"
              ></div>
            </div>
            <span class="text-xs text-white">{{ day.high }}°</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Farming Tips -->
    <div class="p-5 border-t border-white/5 bg-[#5cb83a]/5">
      <p class="text-[10px] text-[#5cb83a] font-bold uppercase tracking-wider mb-2">Today's Tip</p>
      <p class="text-xs text-white/60">
        Good conditions for harvesting. Avoid watering crops during peak sunlight hours (12-3 PM) to reduce evaporation.
      </p>
    </div>
  </div>
</template>