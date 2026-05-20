<script setup>
import { ref, computed, onMounted } from 'vue';
import { 
  TrendingUp, TrendingDown, Package, Users, 
  Naira, Calendar, ArrowUp, ArrowDown, 
  BarChart3, PieChart, Activity
} from 'lucide-vue-next';

const props = defineProps({
  period: {
    type: String,
    default: '7d' // 7d, 30d, 90d, 1y
  }
});

// Mock analytics data
const analyticsData = ref({
  revenue: {
    current: 245000,
    previous: 198000,
    trend: 'up'
  },
  orders: {
    current: 47,
    previous: 38,
    trend: 'up'
  },
  customers: {
    current: 23,
    previous: 19,
    trend: 'up'
  },
  avgOrderValue: {
    current: 5212,
    previous: 4892,
    trend: 'up'
  },
  productsSold: {
    current: 156,
    previous: 124,
    trend: 'up'
  },
  conversionRate: {
    current: 73,
    previous: 68,
    trend: 'up'
  }
});

// Revenue by period data
const revenueByPeriod = computed(() => {
  const data = {
    '7d': [
      { day: 'Mon', value: 35000 },
      { day: 'Tue', value: 28000 },
      { day: 'Wed', value: 42000 },
      { day: 'Thu', value: 31000 },
      { day: 'Fri', value: 45000 },
      { day: 'Sat', value: 38000 },
      { day: 'Sun', value: 26000 },
    ],
    '30d': [
      { week: 'Week 1', value: 180000 },
      { week: 'Week 2', value: 210000 },
      { week: 'Week 3', value: 195000 },
      { week: 'Week 4', value: 245000 },
    ]
  };
  return data[props.period] || data['7d'];
});

// Top products
const topProducts = ref([
  { name: 'Zaria Tomatoes', sold: 45, revenue: 69750 },
  { name: 'Kaduna Maize', sold: 38, revenue: 45600 },
  { name: 'Fresh Pepper', sold: 32, revenue: 38400 },
  { name: 'Green Beans', sold: 28, revenue: 33600 },
  { name: 'Sweet Potato', sold: 13, revenue: 11700 },
]);

// Calculate percentage change
const percentChange = (current, previous) => {
  if (previous === 0) return 100;
  return Math.round(((current - previous) / previous) * 100);
};

const formatCurrency = (value) => {
  return new Intl.NumberFormat('en-NG', {
    style: 'currency',
    currency: 'NGN',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(value);
};
</script>

<template>
  <div class="space-y-6">
    <!-- Key Metrics Cards -->
    <div class="grid grid-cols-2 lg:grid-cols-4 gap-4">
      <!-- Revenue -->
      <div class="bg-[#0d2010] border border-white/10 rounded-2xl p-4">
        <div class="flex items-center justify-between mb-3">
          <div class="p-2 bg-[#5cb83a]/10 rounded-xl">
            <Naira :size="18" class="text-[#5cb83a]" />
          </div>
          <span 
            class="flex items-center gap-1 text-[10px] font-bold"
            :class="analyticsData.revenue.trend === 'up' ? 'text-[#5cb83a]' : 'text-red-400'"
          >
            <ArrowUp v-if="analyticsData.revenue.trend === 'up'" :size="12" />
            <ArrowDown v-else :size="12" />
            {{ percentChange(analyticsData.revenue.current, analyticsData.revenue.previous) }}%
          </span>
        </div>
        <p class="text-xl font-serif text-white">{{ formatCurrency(analyticsData.revenue.current) }}</p>
        <p class="text-[10px] text-white/40 uppercase mt-1">Revenue</p>
      </div>

      <!-- Orders -->
      <div class="bg-[#0d2010] border border-white/10 rounded-2xl p-4">
        <div class="flex items-center justify-between mb-3">
          <div class="p-2 bg-blue-500/10 rounded-xl">
            <Package :size="18" class="text-blue-400" />
          </div>
          <span 
            class="flex items-center gap-1 text-[10px] font-bold"
            :class="analyticsData.orders.trend === 'up' ? 'text-[#5cb83a]' : 'text-red-400'"
          >
            <ArrowUp v-if="analyticsData.orders.trend === 'up'" :size="12" />
            {{ percentChange(analyticsData.orders.current, analyticsData.orders.previous) }}%
          </span>
        </div>
        <p class="text-xl font-serif text-white">{{ analyticsData.orders.current }}</p>
        <p class="text-[10px] text-white/40 uppercase mt-1">Orders</p>
      </div>

      <!-- Customers -->
      <div class="bg-[#0d2010] border border-white/10 rounded-2xl p-4">
        <div class="flex items-center justify-between mb-3">
          <div class="p-2 bg-purple-500/10 rounded-xl">
            <Users :size="18" class="text-purple-400" />
          </div>
          <span 
            class="flex items-center gap-1 text-[10px] font-bold"
            :class="analyticsData.customers.trend === 'up' ? 'text-[#5cb83a]' : 'text-red-400'"
          >
            <ArrowUp v-if="analyticsData.customers.trend === 'up'" :size="12" />
            {{ percentChange(analyticsData.customers.current, analyticsData.customers.previous) }}%
          </span>
        </div>
        <p class="text-xl font-serif text-white">{{ analyticsData.customers.current }}</p>
        <p class="text-[10px] text-white/40 uppercase mt-1">Buyers</p>
      </div>

      <!-- Avg Order Value -->
      <div class="bg-[#0d2010] border border-white/10 rounded-2xl p-4">
        <div class="flex items-center justify-between mb-3">
          <div class="p-2 bg-amber-500/10 rounded-xl">
            <Activity :size="18" class="text-amber-400" />
          </div>
          <span 
            class="flex items-center gap-1 text-[10px] font-bold"
            :class="analyticsData.avgOrderValue.trend === 'up' ? 'text-[#5cb83a]' : 'text-red-400'"
          >
            <ArrowUp v-if="analyticsData.avgOrderValue.trend === 'up'" :size="12" />
            {{ percentChange(analyticsData.avgOrderValue.current, analyticsData.avgOrderValue.previous) }}%
          </span>
        </div>
        <p class="text-xl font-serif text-white">{{ formatCurrency(analyticsData.avgOrderValue.current) }}</p>
        <p class="text-[10px] text-white/40 uppercase mt-1">Avg Order</p>
      </div>
    </div>

    <!-- Charts Section -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <!-- Revenue Chart -->
      <div class="bg-[#0d2010] border border-white/10 rounded-2xl p-5">
        <div class="flex justify-between items-center mb-6">
          <h3 class="text-sm font-bold text-white flex items-center gap-2">
            <BarChart3 :size="16" class="text-[#5cb83a]" />
            Revenue Trend
          </h3>
          <div class="flex gap-2">
            <button 
              v-for="p in ['7d', '30d']" 
              :key="p"
              @click="$emit('period-change', p)"
              class="px-3 py-1 text-[10px] font-bold uppercase rounded-lg transition-colors"
              :class="period === p ? 'bg-[#5cb83a] text-black' : 'bg-white/5 text-white/40 hover:text-white'"
            >
              {{ p }}
            </button>
          </div>
        </div>

        <!-- Bar Chart Visualization -->
        <div class="h-48 flex items-end gap-2">
          <div 
            v-for="(item, index) in revenueByPeriod" 
            :key="index"
            class="flex-1 flex flex-col items-center gap-2"
          >
            <div 
              class="w-full bg-[#5cb83a]/20 rounded-t-lg relative overflow-hidden group"
              :style="{ height: `${(item.value / Math.max(...revenueByPeriod.map(d => d.value))) * 100}%` }"
            >
              <div 
                class="absolute bottom-0 left-0 right-0 bg-[#5cb83a] rounded-t-lg transition-all group-hover:bg-[#4da330]"
                :style="{ height: '80%' }"
              ></div>
            </div>
            <span class="text-[8px] text-white/30">{{ item.day || item.week }}</span>
          </div>
        </div>
      </div>

      <!-- Top Products -->
      <div class="bg-[#0d2010] border border-white/10 rounded-2xl p-5">
        <h3 class="text-sm font-bold text-white flex items-center gap-2 mb-6">
          <PieChart :size="16" class="text-[#5cb83a]" />
          Top Performing Products
        </h3>

        <div class="space-y-4">
          <div 
            v-for="(product, index) in topProducts" 
            :key="product.name"
            class="flex items-center gap-4"
          >
            <span class="text-[10px] font-bold text-white/30 w-4">{{ index + 1 }}</span>
            <div class="flex-1">
              <div class="flex justify-between items-center mb-1">
                <span class="text-sm font-medium text-white">{{ product.name }}</span>
                <span class="text-xs text-[#5cb83a]">{{ formatCurrency(product.revenue) }}</span>
              </div>
              <div class="h-1.5 bg-white/10 rounded-full overflow-hidden">
                <div 
                  class="h-full bg-[#5cb83a] rounded-full"
                  :style="{ width: `${(product.sold / topProducts[0].sold) * 100}%` }"
                ></div>
              </div>
            </div>
            <span class="text-[10px] text-white/40 w-12 text-right">{{ product.sold }} sold</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Additional Stats -->
    <div class="grid grid-cols-2 lg:grid-cols-3 gap-4">
      <div class="bg-[#0d2010] border border-white/10 rounded-2xl p-4">
        <p class="text-[10px] text-white/40 uppercase mb-2">Products Sold</p>
        <p class="text-2xl font-serif text-white">{{ analyticsData.productsSold.current }}</p>
        <p class="text-[10px] text-[#5cb83a] mt-1">+{{ percentChange(analyticsData.productsSold.current, analyticsData.productsSold.previous) }}% vs last period</p>
      </div>
      <div class="bg-[#0d2010] border border-white/10 rounded-2xl p-4">
        <p class="text-[10px] text-white/40 uppercase mb-2">Conversion Rate</p>
        <p class="text-2xl font-serif text-white">{{ analyticsData.conversionRate.current }}%</p>
        <p class="text-[10px] text-[#5cb83a] mt-1">+{{ percentChange(analyticsData.conversionRate.current, analyticsData.conversionRate.previous) }}% vs last period</p>
      </div>
      <div class="bg-[#0d2010] border border-white/10 rounded-2xl p-4">
        <p class="text-[10px] text-white/40 uppercase mb-2">Repeat Buyers</p>
        <p class="text-2xl font-serif text-white">68%</p>
        <p class="text-[10px] text-white/40 mt-1">Of all buyers</p>
      </div>
    </div>
  </div>
</template>