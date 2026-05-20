<script setup>
import { ref, onMounted, computed } from 'vue';
import { useRouter } from 'vue-router';
import { 
  Users, Package, ShoppingBag, CreditCard, 
  Truck, AlertTriangle, TrendingUp, Loader2,
  ArrowRight, RefreshCw, ShieldCheck, DollarSign
} from 'lucide-vue-next';
import { getAdminDashboardCounts } from '@/api/api';

const router = useRouter();
const isLoading = ref(true);
const stats = ref({
  buyers: 0,
  farmers: 0,
  dispatch_riders: 0,
  orders: 0,
  payments: 0,
  farmer_profiles: 0,
  products: 0,
  pending_disputes: 0
});

const fetchStats = async () => {
  isLoading.value = true;
  try {
    stats.value = await getAdminDashboardCounts();
  } catch (err) {
    console.error("Failed to fetch dashboard stats:", err);
  } finally {
    isLoading.value = false;
  }
};

const statCards = computed(() => [
  {
    title: 'Total Users',
    value: stats.value.buyers + stats.value.farmers + stats.value.dispatch_riders,
    icon: Users,
    color: 'text-blue-400',
    bgColor: 'bg-blue-500/10',
    borderColor: 'border-blue-500/20',
    link: '/admin/all_users'
  },
  {
    title: 'Buyers',
    value: stats.value.buyers,
    icon: ShoppingBag,
    color: 'text-purple-400',
    bgColor: 'bg-purple-500/10',
    borderColor: 'border-purple-500/20',
    link: '/admin/all_users?role=buyer'
  },
  {
    title: 'Farmers',
    value: stats.value.farmers,
    icon: TrendingUp,
    color: 'text-[#5cb83a]',
    bgColor: 'bg-[#5cb83a]/10',
    borderColor: 'border-[#5cb83a]/20',
    link: '/admin/all_farmer_profile'
  },
  {
    title: 'Dispatch Riders',
    value: stats.value.dispatch_riders,
    icon: Truck,
    color: 'text-amber-400',
    bgColor: 'bg-amber-500/10',
    borderColor: 'border-amber-500/20',
    link: '/admin/dispatch-riders'
  },
  {
    title: 'Total Orders',
    value: stats.value.orders,
    icon: Package,
    color: 'text-white/60',
    bgColor: 'bg-white/5',
    borderColor: 'border-white/10',
    link: '/admin/orders'
  },
  {
    title: 'Total Products',
    value: stats.value.products,
    icon: ShieldCheck,
    color: 'text-cyan-400',
    bgColor: 'bg-cyan-500/10',
    borderColor: 'border-cyan-500/20',
    link: '/admin/all_products'
  },
  {
    title: 'Total Payments',
    value: stats.value.payments,
    icon: DollarSign,
    color: 'text-green-400',
    bgColor: 'bg-green-500/10',
    borderColor: 'border-green-500/20',
    link: '/admin/all_payments'
  },
  {
    title: 'Pending Disputes',
    value: stats.value.pending_disputes,
    icon: AlertTriangle,
    color: 'text-red-400',
    bgColor: 'bg-red-500/10',
    borderColor: 'border-red-500/20',
    link: '/admin/disputes',
    alert: stats.value.pending_disputes > 0
  }
]);

onMounted(fetchStats);
</script>

<template>
  <div class="p-6">
    <!-- Header -->
    <div class="flex justify-between items-center mb-8">
      <div>
        <h1 class="text-2xl font-bold text-white">Admin Dashboard</h1>
        <p class="text-white/40 text-sm">Platform overview and key metrics</p>
      </div>
      <button 
        @click="fetchStats" 
        :disabled="isLoading"
        class="p-3 bg-white/5 border border-white/10 rounded-xl hover:border-[#5cb83a]/50 transition-all"
      >
        <RefreshCw :size="18" :class="{ 'animate-spin': isLoading }" class="text-white/40" />
      </button>
    </div>

    <!-- Loading State -->
    <div v-if="isLoading" class="flex flex-col items-center justify-center py-24">
      <Loader2 class="animate-spin text-[#5cb83a] mb-4" :size="40" />
      <p class="text-white/40">Loading dashboard data...</p>
    </div>

    <!-- Stats Grid -->
    <div v-else class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
      <div 
        v-for="card in statCards" 
        :key="card.title"
        @click="router.push(card.link)"
        class="bg-[#0d2010] border rounded-2xl p-5 cursor-pointer transition-all hover:scale-[1.02] hover:border-[#5cb83a]/30 group"
        :class="card.borderColor"
      >
        <div class="flex justify-between items-start mb-4">
          <div class="p-2.5 rounded-xl" :class="card.bgColor">
            <component :is="card.icon" :size="22" :class="card.color" />
          </div>
          <ArrowRight :size="16" class="text-white/20 group-hover:text-[#5cb83a] transition-colors" />
        </div>
        <p class="text-3xl font-serif mb-1" :class="card.alert ? 'text-red-400' : 'text-white'">
          {{ card.value }}
        </p>
        <p class="text-[10px] uppercase tracking-widest text-white/40 font-bold">{{ card.title }}</p>
      </div>
    </div>

    <!-- Quick Actions -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <!-- Recent Activity / Quick Links -->
      <div class="bg-[#0d2010] border border-white/10 rounded-2xl p-6">
        <h2 class="text-lg font-bold mb-6">Quick Actions</h2>
        
        <div class="space-y-3">
          <button 
            v-for="action in [
              { label: 'Manage Dispatch Riders', icon: Truck, link: '/admin/dispatch-riders' },
              { label: 'View All Orders', icon: Package, link: '/admin/orders' },
              { label: 'Resolve Disputes', icon: AlertTriangle, link: '/admin/disputes', alert: stats.pending_disputes > 0 },
              { label: 'Manage Users', icon: Users, link: '/admin/all_users' },
            ]"
            :key="action.label"
            @click="router.push(action.link)"
            class="w-full flex items-center justify-between p-4 bg-white/5 border border-white/10 rounded-xl hover:bg-white/10 hover:border-[#5cb83a]/30 transition-all group"
          >
            <div class="flex items-center gap-3">
              <component :is="action.icon" :size="18" :class="action.alert ? 'text-red-400' : 'text-white/40'" />
              <span class="text-sm font-medium">{{ action.label }}</span>
            </div>
            <ArrowRight :size="16" class="text-white/20 group-hover:text-[#5cb83a]" />
          </button>
        </div>
      </div>

      <!-- Platform Health -->
      <div class="bg-[#0d2010] border border-white/10 rounded-2xl p-6">
        <h2 class="text-lg font-bold mb-6">Platform Health</h2>
        
        <div class="space-y-4">
          <div class="flex items-center justify-between p-4 bg-white/5 rounded-xl">
            <div class="flex items-center gap-3">
              <div class="w-3 h-3 rounded-full bg-[#5cb83a]"></div>
              <span class="text-sm">API Services</span>
            </div>
            <span class="text-[10px] font-bold text-[#5cb83a] uppercase">Operational</span>
          </div>
          
          <div class="flex items-center justify-between p-4 bg-white/5 rounded-xl">
            <div class="flex items-center gap-3">
              <div class="w-3 h-3 rounded-full bg-[#5cb83a]"></div>
              <span class="text-sm">Payment Gateway</span>
            </div>
            <span class="text-[10px] font-bold text-[#5cb83a] uppercase">Active</span>
          </div>
          
          <div class="flex items-center justify-between p-4 bg-white/5 rounded-xl">
            <div class="flex items-center gap-3">
              <div class="w-3 h-3 rounded-full bg-[#5cb83a]"></div>
              <span class="text-sm">Database</span>
            </div>
            <span class="text-[10px] font-bold text-[#5cb83a] uppercase">Connected</span>
          </div>
          
          <div class="flex items-center justify-between p-4 bg-white/5 rounded-xl">
            <div class="flex items-center gap-3">
              <div class="w-3 h-3 rounded-full" :class="stats.pending_disputes > 0 ? 'bg-amber-500' : 'bg-[#5cb83a]'"></div>
              <span class="text-sm">Pending Issues</span>
            </div>
            <span class="text-[10px] font-bold" :class="stats.pending_disputes > 0 ? 'text-amber-500' : 'text-[#5cb83a]'">
              {{ stats.pending_disputes }} {{ stats.pending_disputes === 1 ? 'issue' : 'issues' }}
            </span>
          </div>
        </div>
      </div>
    </div>

    <!-- System Info -->
    <div class="mt-6 p-4 bg-white/5 border border-white/10 rounded-xl flex items-center justify-between">
      <div class="flex items-center gap-3">
        <ShieldCheck class="text-[#5cb83a]" :size="20" />
        <span class="text-sm text-white/60">FarmPay Admin Platform</span>
      </div>
      <span class="text-[10px] text-white/30 uppercase tracking-wider">v1.0.0</span>
    </div>
  </div>
</template>