<script setup>
import { ref } from 'vue';
import {
  Wallet, Truck, ArrowRight,
  TrendingUp, Users, CheckCircle2,
  Camera, Microscope, Lock, ShieldCheck
} from 'lucide-vue-next';

const stats = ref([
  { label: 'Total Payouts', value: '₦14.2M', icon: TrendingUp },
  { label: 'Verified Products', value: '847', icon: ShieldCheck },
  { label: 'Active Farmers', value: '1,203', icon: Users },
  { label: 'Delivery Rate', value: '99.1%', icon: Truck }
]);

const steps = ref([
  { 
    id: 1, 
    icon: Camera, 
    title: 'Upload Produce', 
    desc: 'Farmer uploads image and sets their own fair price.' 
  },
  { 
    id: 2, 
    icon: Microscope, 
    title: 'AI Quality Scan', 
    desc: 'Our vision AI verifies the harvest quality instantly.' 
  },
  { 
    id: 3, 
    icon: Wallet, // The Pay aspect
    title: 'Secure FarmPay', 
    desc: 'Money is held in escrow. Safe for buyers, guaranteed for farmers.' 
  },
  { 
    id: 4, 
    icon: CheckCircle2, 
    title: 'Instant Payout', 
    desc: 'Once OTP is verified at delivery, the farmer is paid immediately.' 
  }
]);
</script>

<template>
  <div class="min-h-screen bg-[#061209] text-[#f0ede4] font-sans selection:bg-[#5cb83a]/30">
    <nav class="flex justify-between items-center py-5 px-6 md:px-12 border-b border-white/10">
      <div class="flex items-center gap-3">
        <div class="w-9 h-9 bg-[#2d7a18] rounded-full flex items-center justify-center">
          <Wallet class="text-white" :size="18" />
        </div>
        <span class="text-xl font-semibold tracking-tight">
          FarmPay<span class="text-[#5cb83a]">.</span>ng
        </span>
      </div>
      <div class="flex items-center gap-4">
        <router-link to="/login" class="text-sm font-medium text-white/50 hover:text-white transition-colors">Sign in</router-link>
        <router-link to="/signup" class="bg-[#2d7a18] hover:bg-[#3a9e20] text-white px-5 py-2.5 rounded-lg text-sm font-semibold transition-all">
          Get started
        </router-link>
      </div>
    </nav>

    <main class="max-w-7xl mx-auto px-6 md:px-12 py-16 md:py-24">
      <div class="grid grid-cols-1 lg:grid-cols-12 gap-16 items-start">
        
        <div class="lg:col-span-7 space-y-8 text-center lg:text-left">
          <span class="inline-flex items-center px-3 py-1 rounded-full bg-[#5cb83a]/10 border border-[#5cb83a]/20 text-[#7bc95a] text-xs font-semibold tracking-wider uppercase">
            Kaduna State · Secure Agricultural Payments
          </span>
          
          <h1 class="font-serif text-5xl md:text-7xl leading-[1.1] tracking-tight">
            The way farmers<br />
            <span class="text-[#5cb83a] italic">get paid.</span>
          </h1>
          
          <p class="text-white/50 text-lg leading-relaxed max-w-lg mx-auto lg:mx-0">
            Secure agricultural commerce. Farmers set the price, we handle the verification and the escrow. Trust-less trading from farm to doorstep.
          </p>

          <div class="flex flex-wrap justify-center lg:justify-start gap-4 pt-4">
            <router-link to="/signup" class="group bg-[#2d7a18] text-white px-8 py-4 rounded-xl font-bold text-lg flex items-center gap-2 hover:bg-[#3a9e20] transition-all">
              Start Selling
              <ArrowRight class="group-hover:translate-x-1 transition-transform" />
            </router-link>
            <router-link to="/marketplace" class="border border-white/10 bg-white/5 text-white px-8 py-4 rounded-xl font-bold text-lg hover:bg-white/10 transition-all">
              Buy Produce
            </router-link>
          </div>
        </div>

        <div class="lg:col-span-5 w-full">
          <div class="bg-white/5 border border-white/10 rounded-3xl p-8 backdrop-blur-sm relative overflow-hidden">
            <div class="text-[10px] uppercase tracking-[2px] text-white/30 font-bold mb-8">FarmPay Ecosystem Activity</div>
            
            <div class="grid grid-cols-2 gap-y-10 gap-x-6 mb-10">
              <div v-for="stat in stats" :key="stat.label">
                <div class="flex items-center gap-2 text-[#7bc95a] mb-1">
                  <component :is="stat.icon" :size="14" />
                  <span class="text-[10px] uppercase font-bold tracking-wider opacity-60">{{ stat.label }}</span>
                </div>
                <div class="font-serif text-3xl font-medium">{{ stat.value }}</div>
              </div>
            </div>

            <div class="bg-[#3a8f22]/10 border border-[#5cb83a]/20 rounded-2xl p-5 flex gap-4 text-left">
              <div class="mt-1 text-[#5cb83a]"><Lock :size="18" /></div>
              <div class="text-sm">
                <strong class="text-[#7bc95a] block mb-1">Escrow Security Active</strong>
                <span class="text-white/40 leading-snug">
                  Payments are only released to farmers after the buyer confirms the OTP at the drop-off zone.
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <section class="mt-32 pt-20 border-t border-white/5">
        <div class="text-[10px] uppercase tracking-[3px] text-white/20 font-bold mb-12 text-center">The FarmPay Protocol</div>
        
        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-12">
          <div v-for="step in steps" :key="step.id" class="space-y-4 group">
            <div class="w-14 h-14 bg-white/5 border border-white/10 rounded-2xl flex items-center justify-center group-hover:border-[#5cb83a]/30 transition-colors">
              <component :is="step.icon" class="text-[#5cb83a]" :size="28" />
            </div>
            <div class="space-y-1 text-left">
              <span class="text-[10px] text-[#5cb83a] font-bold uppercase tracking-widest text-left">Phase 0{{ step.id }}</span>
              <h3 class="font-bold text-lg">{{ step.title }}</h3>
              <p class="text-sm text-white/40 leading-relaxed">{{ step.desc }}</p>
            </div>
          </div>
        </div>
      </section>
    </main>

    <footer class="py-12 text-center border-t border-white/5">
      <p class="text-[10px] text-white/20 tracking-widest uppercase">© 2026 FarmPay.ng · The Future of Agri-Payments</p>
    </footer>
  </div>
</template>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display:ital@0;1&family=DM+Sans:wght@300;400;500;600&display=swap');

.font-serif { font-family: 'DM Serif Display', serif; }
.font-sans { font-family: 'DM Sans', sans-serif; }
</style>