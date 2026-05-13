<script setup>
import { 
  ShoppingCart, Calendar, MapPin, 
  ExternalLink, Copy, Check 
} from 'lucide-vue-next';
import { ref } from 'vue';

const props = defineProps({
  orders: Array,
  currentPage: Number,
  totalPages: Number
});

const emit = defineEmits(['view', 'changePage']);

// State to show a temporary "Check" icon when copied
const copiedId = ref(null);

const copyToClipboard = async (id) => {
  try {
    await navigator.clipboard.writeText(id);
    copiedId.value = id;
    setTimeout(() => { copiedId.value = null; }, 2000);
  } catch (err) {
    console.error('Failed to copy!', err);
  }
};

const formatCurrency = (value) => {
  return new Intl.NumberFormat('en-NG', {
    style: 'currency',
    currency: 'NGN',
  }).format(value);
};
</script>

<template>
  <div class="w-full space-y-4">
    <div class="w-full overflow-x-auto rounded-2xl border border-white/10 bg-white/5 backdrop-blur-sm">
      <table class="w-full text-left border-collapse">
        <thead>
          <tr class="border-b border-white/10 bg-white/5">
            <th class="px-6 py-4 text-xs font-bold uppercase tracking-widest text-[#7bc95a]">Order Details</th>
            <th class="px-6 py-4 text-xs font-bold uppercase tracking-widest text-[#7bc95a]">Location</th>
            <th class="px-6 py-4 text-xs font-bold uppercase tracking-widest text-[#7bc95a]">Amount</th>
            <th class="px-6 py-4 text-xs font-bold uppercase tracking-widest text-[#7bc95a]">Status</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-white/5">
          <tr v-for="order in orders" :key="order.id" class="hover:bg-white/2 transition-colors group">
            <td class="px-6 py-4">
              <div class="flex items-center gap-3">
                <div class="w-10 h-10 rounded-xl bg-[#2d7a18]/10 flex items-center justify-center text-[#7bc95a]">
                  <ShoppingCart :size="18" />
                </div>
                <div>
                  <div class="flex items-center gap-2">
                    <p class="text-sm font-mono text-white font-medium">#{{ order.id?.slice(0, 8) }}</p>
                    <button 
                      @click="copyToClipboard(order.id)" 
                      class="hover:text-[#7bc95a] transition-colors text-white/20"
                      title="Copy Order ID"
                    >
                      <Check v-if="copiedId === order.id" :size="14" class="text-[#7bc95a]" />
                      <Copy v-else :size="14" />
                    </button>
                  </div>
                  <div class="flex items-center gap-1 text-[10px] text-white/40 uppercase font-bold">
                    <Calendar :size="10" />
                    {{ new Date(order.created_at).toLocaleDateString() }}
                  </div>
                </div>
              </div>
            </td>
            
            <td class="px-6 py-4">
              <div class="flex items-center gap-2 text-sm text-white/60 capitalize">
                <MapPin :size="14" class="text-white/20" />
                {{ order.delivery_location?.replace('_', ' ') }}
              </div>
            </td>

            <td class="px-6 py-4">
              <div class="text-sm font-bold text-white">
                {{ formatCurrency(order.total_amount) }}
              </div>
              <p class="text-[10px] text-white/30">Fee: {{ formatCurrency(order.delivery_fee) }}</p>
            </td>

            <td class="px-6 py-4">
              <span 
                class="inline-flex items-center px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase border"
                :class="order.status === 'pending' ? 'bg-orange-500/10 border-orange-500/20 text-orange-400' : 'bg-[#5cb83a]/10 border-[#5cb83a]/20 text-[#7bc95a]'"
              >
                {{ order.status }}
              </span>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>