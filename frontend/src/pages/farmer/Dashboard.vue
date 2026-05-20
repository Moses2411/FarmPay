<script setup>
import { ref, computed, onMounted } from 'vue';
import { useAuthStore } from '../../stores/auth';
import { useRouter } from 'vue-router';
import api from '@/api/api';
import {
  LayoutDashboard, PlusCircle, Package,
  Wallet, History, Settings, LogOut, ShoppingBag,
  ShieldAlert, TrendingUp, CheckCircle2,
  Clock, ChevronRight
} from 'lucide-vue-next';

import AddProductModal from '../../components/farmer/AddProductModal.vue';
import FarmAnalytics from '@/components/analytics/FarmAnalytics.vue';
import WeatherWidget from '@/components/analytics/WeatherWidget.vue';

const auth = useAuthStore();
const router = useRouter();
const selectedPeriod = ref('7d');

const userName = computed(() => auth.user?.fullName || 'Farmer');
const isVerified = computed(() => auth.user?.isVerified || false);

// Reactive stats
const stats = ref([
  { label: 'Total Sales', value: '₦0', icon: Wallet, color: 'text-blue-400' },
  { label: 'Active Listings', value: '0', icon: Package, color: 'text-[#5cb83a]' },
  { label: 'Pending Delivery', value: '0', icon: Clock, color: 'text-amber-500' },
  { label: 'Trust Rating', value: '100%', icon: TrendingUp, color: 'text-purple-400' },
]);

const recentOrders = ref([]);
const isAddModalOpen = ref(false);

const fetchFarmerData = async () => {
  try {
    const orders = await api.get('/orders/farmer-orders');

    recentOrders.value = (orders.slice || orders).slice(0, 5).map(order => ({
      id: order.id || order.order_id,
      buyer: order.buyer_name,
      price: `₦${(order.total_amount || 0).toLocaleString()}`,
      status: order.status,
      produce: order.items?.[0]?.product?.name || 'Farm Produce'
    }));

    const totalRevenue = orders.reduce((sum, o) => sum + (o.total_amount || 0), 0);
    stats.value[0].value = `₦${totalRevenue.toLocaleString()}`;

    const pendingCount = orders.filter(o => o.status === 'pending' || o.status === 'paid').length;
    stats.value[2].value = pendingCount.toString();

  } catch (err) {
    console.warn("Farmer data fetch failed.");
  }
};

const refreshData = () => fetchFarmerData();

onMounted(fetchFarmerData);
</script>

<template>
  <div class="min-h-screen bg-[#061209] flex text-[#f0ede4] font-sans">
    
    <aside class="w-64 border-r border-white/5 bg-[#0d2010] flex flex-col">
      <div class="p-6 flex items-center gap-3">
        <div class="w-8 h-8 bg-[#2d7a18] rounded-full flex items-center justify-center">
          <Wallet class="text-white" :size="16" />
        </div>
        <span class="font-serif text-xl font-semibold">FarmPay<span class="text-[#5cb83a]">.</span></span>
      </div>

      <nav class="flex-1 px-4 space-y-2 mt-4">
        <router-link to="/farmer" class="flex items-center gap-3 px-4 py-3 rounded-xl bg-[#5cb83a]/10 text-[#5cb83a] font-bold">
          <LayoutDashboard :size="20" /> Dashboard
        </router-link>
        <router-link to="/marketplace" class="flex items-center gap-3 px-4 py-3 rounded-xl text-white/40 hover:bg-white/5 hover:text-white transition-all">
          <ShoppingBag :size="20" /> Market View
        </router-link>
        <router-link v-for="link in [
          { to: '/farmer/inventory', icon: Package, label: 'My Harvest' },
          { to: '/farmer/payouts', icon: Wallet, label: 'Payouts' },
          { to: '/farmer/history', icon: History, label: 'Order History' }
        ]" :key="link.to" :to="link.to" class="flex items-center gap-3 px-4 py-3 rounded-xl text-white/40 hover:bg-white/5 hover:text-white transition-all">
          <component :is="link.icon" :size="20" /> {{ link.label }}
        </router-link>
      </nav>

      <div class="p-4 border-t border-white/5">
        <button @click="auth.logout" class="flex items-center gap-3 px-4 py-3 w-full text-red-400/60 hover:text-red-400 hover:bg-red-400/5 rounded-xl transition-all">
          <LogOut :size="20" /> Logout
        </button>
      </div>
    </aside>

    <main class="flex-1 flex flex-col">
      <header class="h-20 border-b border-white/5 flex items-center justify-between px-8 bg-[#061209]/50 backdrop-blur-md sticky top-0 z-10">
        <div>
          <h2 class="text-sm font-bold text-white/40 uppercase tracking-widest">Welcome back,</h2>
          <p class="text-xl font-serif">{{ userName }}</p>
        </div>
        <div class="flex items-center gap-4">
          <button @click="router.push('/marketplace')" class="hidden lg:flex items-center gap-2 px-4 py-2 bg-white/5 border border-white/10 rounded-xl text-xs font-bold uppercase tracking-widest hover:bg-white/10 transition-all cursor-pointer">
             <ShoppingBag :size="14" /> Market View
          </button>
          <div v-if="isVerified" class="flex items-center gap-2 px-3 py-1 bg-[#5cb83a]/10 border border-[#5cb83a]/20 rounded-full text-[#5cb83a] text-[10px] font-bold uppercase">
            <CheckCircle2 :size="12" /> Verified Farmer
          </div>
          <button class="w-10 h-10 rounded-full bg-white/5 border border-white/10 flex items-center justify-center hover:bg-white/10 transition-all">
            <Settings :size="18" class="text-white/60" />
          </button>
        </div>
      </header>

      <div class="p-8 space-y-8">
        <div v-if="!isVerified" class="bg-[#e6a817]/10 border border-[#e6a817]/20 p-6 rounded-2xl flex items-center justify-between">
          <div class="flex gap-4">
            <div class="w-12 h-12 bg-[#e6a817]/20 rounded-xl flex items-center justify-center text-[#e6a817]">
              <ShieldAlert :size="24" />
            </div>
            <div>
              <h3 class="font-bold text-[#e6a817]">Account Pending Verification</h3>
              <p class="text-sm text-[#e6a817]/60">You must complete NIN/BVN verification before listing products.</p>
            </div>
          </div>
          <router-link to="/complete-profile" class="bg-[#e6a817] text-black px-6 py-2.5 rounded-lg font-bold text-sm hover:bg-[#ffbc26] transition-all">
            Complete Now
          </router-link>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <div v-for="s in stats" :key="s.label" class="bg-white/5 border border-white/10 p-6 rounded-2xl">
            <div class="flex justify-between items-start mb-4">
              <div class="p-2 bg-white/5 rounded-lg" :class="s.color">
                <component :is="s.icon" :size="20" />
              </div>
              <span class="text-[10px] text-white/20 font-bold uppercase tracking-wider">Live</span>
            </div>
            <p class="text-white/40 text-xs font-bold uppercase tracking-widest mb-1">{{ s.label }}</p>
            <p class="text-2xl font-serif">{{ s.value }}</p>
          </div>
        </div>

        <!-- Analytics & Weather Section -->
        <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div class="lg:col-span-2">
            <FarmAnalytics :period="selectedPeriod" @period-change="p => selectedPeriod = p" />
          </div>
          <div>
            <WeatherWidget location="Kaduna" />
          </div>
        </div>

        <div class="grid grid-cols-1 lg:grid-cols-3 gap-8">
          <div class="lg:col-span-2 bg-white/5 border border-white/10 rounded-3xl overflow-hidden">
            <div class="p-6 border-b border-white/5 flex justify-between items-center">
              <h3 class="font-serif text-lg">Recent Sales</h3>
              <router-link to="/farmer/history" class="text-[10px] uppercase font-bold text-[#5cb83a] hover:underline">View All</router-link>
            </div>
            <div class="overflow-x-auto">
              <table class="w-full text-left">
                <thead class="text-[10px] uppercase text-white/20 font-bold border-b border-white/5">
                  <tr>
                    <th class="px-6 py-4">Buyer</th>
                    <th class="px-6 py-4">Produce</th>
                    <th class="px-6 py-4">Amount</th>
                    <th class="px-6 py-4">Status</th>
                    <th class="px-6 py-4 text-right">Action</th>
                  </tr>
                </thead>
                <tbody class="text-sm">
                  <tr v-for="order in recentOrders" :key="order.id" class="border-b border-white/5 hover:bg-white/5 transition-colors">
                    <td class="px-6 py-4">
                      <p class="font-bold text-white/80">{{ order.buyer }}</p>
                      <p class="text-[10px] font-mono text-white/20">#{{ order.id.slice(-6) }}</p>
                    </td>
                    <td class="px-6 py-4 font-medium">{{ order.produce }}</td>
                    <td class="px-6 py-4 text-[#5cb83a] font-bold">{{ order.price }}</td>
                    <td class="px-6 py-4">
                      <span class="px-2 py-1 rounded-md text-[9px] font-bold uppercase tracking-tighter"
                        :class="order.status === 'completed' ? 'bg-[#5cb83a]/10 text-[#5cb83a]' : 'bg-amber-500/10 text-amber-500'">
                        {{ order.status }}
                      </span>
                    </td>
                    <td class="px-6 py-4 text-right">
                      <button class="p-2 hover:bg-white/10 rounded-lg transition-all cursor-pointer">
                        <ChevronRight :size="16" />
                      </button>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          <div class="bg-[#2d7a18]/10 border border-[#2d7a18]/30 rounded-3xl p-8 flex flex-col justify-between relative overflow-hidden group">
            <div class="absolute top-0 right-0 p-8 text-[#5cb83a]/20 group-hover:scale-110 transition-transform">
              <PlusCircle :size="120" />
            </div>
            <div class="relative z-10">
              <h3 class="text-2xl font-serif mb-4">Ready to sell<br/> your harvest?</h3>
              <p class="text-sm text-white/50 leading-relaxed mb-8">
                Every listing is verified by our system to ensure quality for buyers.
              </p>
            </div>
            <button @click="isAddModalOpen = true"
              :disabled="!isVerified"
              class="relative z-10 w-full bg-[#2d7a18] disabled:bg-white/5 disabled:text-white/20 text-white py-4 rounded-xl font-bold flex items-center justify-center gap-2 hover:bg-[#3a9e20] transition-all"
            >
              <PlusCircle :size="20" />
              List New Produce
            </button>

            <AddProductModal 
              :is-open="isAddModalOpen" 
              @close="isAddModalOpen = false" 
              @refresh="refreshData"
            />
          </div>
        </div>
      </div>
    </main>
  </div>
</template>