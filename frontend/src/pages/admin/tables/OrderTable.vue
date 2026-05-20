<script setup>
import { 
  ShoppingCart, Calendar, MapPin, 
  Copy, Check, Package, User, Wallet
} from 'lucide-vue-next';
import { ref } from 'vue';

const props = defineProps({
  orders: {
    type: Array,
    required: true,
    default: () => []
  },
  currentPage: Number,
  totalPages: Number
});

const emit = defineEmits(['view', 'changePage']);

const copiedId = ref(null);

const copyToClipboard = async (text) => {
  try {
    await navigator.clipboard.writeText(text);
    copiedId.value = text;
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

const getStatusStyles = (status) => {
  switch (status) {
    case 'completed':
    case 'delivered':
      return 'bg-emerald-500/10 border-emerald-500/20 text-emerald-400';
    case 'pending':
    case 'processing':
      return 'bg-orange-500/10 border-orange-500/20 text-orange-400';
    case 'cancelled':
      return 'bg-red-500/10 border-red-500/20 text-red-400';
    default:
      return 'bg-white/10 border-white/20 text-white/60';
  }
};
</script>

<template>
  <div class="w-full space-y-4">
    <div class="w-full overflow-x-auto rounded-2xl border border-white/10 bg-white/5 backdrop-blur-sm">
      <table class="w-full text-left border-collapse">
        <thead>
          <tr class="border-b border-white/10 bg-white/5 text-[10px] font-bold uppercase tracking-widest text-[#7bc95a]">
            <th class="px-6 py-4">Order & Buyer Info</th>
            <th class="px-6 py-4">Destination</th>
            <th class="px-6 py-4">Financials</th>
            <th class="px-6 py-4">Status</th>
            <th class="px-6 py-4">Date</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-white/5">
          <tr v-for="order in orders" :key="order.id" class="hover:bg-white/2 transition-colors group">
            <td class="px-6 py-4">
              <div class="flex items-start gap-3">
                <div class="w-10 h-10 rounded-xl bg-white/5 border border-white/10 flex items-center justify-center text-white/20">
                  <Package :size="20" />
                </div>
                <div class="flex flex-col">
                  <div class="flex items-center gap-2">
                    <span class="font-bold text-[#f0ede4] text-sm font-mono">#{{ order.id.slice(0, 8) }}</span>
                    <button @click="copyToClipboard(order.id)" class="text-white/10 hover:text-[#7bc95a]">
                      <Check v-if="copiedId === order.id" :size="10" class="text-[#7bc95a]" />
                      <Copy v-else :size="10" />
                    </button>
                  </div>
                  <div class="flex items-center gap-1.5 mt-1">
                    <User :size="10" class="text-white/20" />
                    <span class="text-[10px] text-white/40 font-medium">Buyer: {{ order.buyer_id?.slice(0, 8) }}...</span>
                  </div>
                </div>
              </div>
            </td>

            <td class="px-6 py-4">
              <div class="flex items-center gap-2 text-xs text-white/60 capitalize">
                <MapPin :size="14" class="text-[#7bc95a]/50 shrink-0" />
                <span class="truncate max-w-[150px]">{{ order.delivery_location?.replace('_', ' ') }}</span>
              </div>
            </td>

            <td class="px-6 py-4">
              <div class="flex flex-col gap-0.5">
                <div class="text-sm font-bold text-white">{{ formatCurrency(order.total_amount) }}</div>
                <div class="flex items-center gap-1 text-[9px] text-white/30 uppercase font-bold tracking-tighter">
                  <Wallet :size="10" />
                  Fee: {{ formatCurrency(order.delivery_fee) }}
                </div>
              </div>
            </td>

            <td class="px-6 py-4">
              <span 
                class="inline-flex items-center px-2.5 py-1 rounded-full border text-[9px] font-black uppercase tracking-wider"
                :class="getStatusStyles(order.status)"
              >
                {{ order.status }}
              </span>
            </td>

            <td class="px-6 py-4 text-[11px] text-white/40 font-medium">
              <div class="flex items-center gap-2">
                <Calendar :size="12" />
                {{ new Date(order.created_at).toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' }) }}
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <div class="flex items-center justify-between px-2">
      <p class="text-[10px] text-white/30 font-bold uppercase tracking-widest">
        Showing Page {{ currentPage }} of {{ totalPages }}
      </p>
      <div class="flex gap-2">
        <button 
          @click="emit('changePage', currentPage - 1)" 
          :disabled="currentPage <= 1"
          class="px-4 py-2 text-[10px] font-bold uppercase border border-white/10 rounded-lg text-white/40 disabled:opacity-10 hover:bg-white/5"
        >
          Prev
        </button>
        <button 
          @click="emit('changePage', currentPage + 1)" 
          :disabled="currentPage >= totalPages"
          class="px-4 py-2 text-[10px] font-bold uppercase border border-white/10 rounded-lg text-white/40 disabled:opacity-10 hover:bg-white/5"
        >
          Next
        </button>
      </div>
    </div>
  </div>
</template>