<script setup>
import { 
  Users, 
  Wallet, 
  ShoppingBag, 
  Truck, 
  AlertCircle, 
  UserSquare2,
  LayoutDashboard
} from 'lucide-vue-next';

const navItems = [
  { name: 'Dispatch Riders', route: '/admin/dispatch-riders', icon: Truck },
  { name: 'Orders', route: '/admin/orders', icon: ShoppingBag },
  { name: 'Disputes', route: '/admin/disputes', icon: AlertCircle },
  { name: 'All Users', route: '/admin/all_users', icon: Users },
  { name: 'All Payments', route: '/admin/all_payments', icon: Wallet },
  { name: 'Farmer Profiles', route: '/admin/all_farmer_profile', icon: UserSquare2 },
  { name: 'All Products', route: '/admin/all_products', icon: ShoppingBag },
];
</script>

<template>
  <aside class="w-64 min-h-screen bg-[#061209] border-r border-white/10 flex flex-col">
    <div class="p-6 flex items-center gap-3">
      <div class="w-8 h-8 bg-[#2d7a18] rounded-full flex items-center justify-center">
        <Wallet class="text-white" :size="16" />
      </div>
      <span class="font-bold text-xl text-[#f0ede4]">FarmPay<span class="text-[#5cb83a]">.</span>ng</span>
    </div>

    <nav class="flex-1 px-4 space-y-1">
      <router-link 
        v-for="item in navItems" 
        :key="item.name"
        :to="item.route"
        class="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors text-white/60 hover:text-white hover:bg-white/5"
        active-class="bg-[#2d7a18]/20 !text-[#7bc95a] border border-[#5cb83a]/20"
      >
        <component :is="item.icon" :size="18" />
        {{ item.name }}
      </router-link>
    </nav>

  </aside>
</template>