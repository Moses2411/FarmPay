<script setup>
import { 
  CreditCard, Calendar, Receipt, 
  ExternalLink, Copy, Check, Lock, Unlock, RefreshCcw 
} from 'lucide-vue-next';
import { ref } from 'vue';

const props = defineProps({
  payments: {
    type: Array,
    required: true,
    default: () => []
  },
  currentPage: Number,
  totalPages: Number
});

const emit = defineEmits(['changePage']);

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
    case 'success':
      return 'bg-emerald-500/10 border-emerald-500/20 text-emerald-400';
    case 'pending':
      return 'bg-orange-500/10 border-orange-500/20 text-orange-400';
    case 'failed':
      return 'bg-red-500/10 border-red-500/20 text-red-400';
    default:
      return 'bg-white/10 border-white/20 text-white/60';
  }
};

const getEscrowStyles = (status) => {
  switch (status) {
    case 'held':
      return { class: 'bg-blue-500/10 border-blue-500/20 text-blue-400', icon: Lock };
    case 'released':
      return { class: 'bg-[#5cb83a]/10 border-[#5cb83a]/20 text-[#7bc95a]', icon: Unlock };
    case 'refunded':
      return { class: 'bg-purple-500/10 border-purple-500/20 text-purple-400', icon: RefreshCcw };
    default:
      return { class: 'bg-white/5 border-white/10 text-white/30', icon: Lock };
  }
};
</script>

<template>
  <div class="w-full space-y-4">
    <div class="w-full overflow-x-auto rounded-2xl border border-white/10 bg-white/5 backdrop-blur-sm">
      <table class="w-full text-left border-collapse">
        <thead>
          <tr class="border-b border-white/10 bg-white/5 text-[10px] font-bold uppercase tracking-widest text-[#7bc95a]">
            <th class="px-6 py-4">Reference & Order</th>
            <th class="px-6 py-4">Amount</th>
            <th class="px-6 py-4">Payment Status</th>
            <th class="px-6 py-4">Escrow State</th>
            <th class="px-6 py-4">Date Paid</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-white/5">
          <tr v-for="payment in payments" :key="payment.id" class="hover:bg-white/2 transition-colors group">
            <td class="px-6 py-4">
              <div class="flex flex-col gap-1">
                <div class="flex items-center gap-2">
                  <span class="text-xs font-bold text-[#f0ede4] font-mono">Id:{{ payment.order_id }}</span>
                  <button @click="copyToClipboard(payment.order_id)" class="text-white/10 hover:text-[#7bc95a] transition-colors">
                    <Check v-if="copiedId === payment.payment_reference" :size="12" class="text-[#7bc95a]" />
                    <Copy v-else :size="12" />
                  </button>
                </div>
                <div class="flex items-center gap-1.5 text-[10px] text-white/30 uppercase tracking-tighter">
                  Order: {{ payment.payment_reference }}
                </div>
              </div>
            </td>

            <td class="px-6 py-4">
              <div class="text-sm font-bold text-white">
                {{ formatCurrency(payment.amount) }}
              </div>
              <div class="text-[9px] text-white/20 uppercase font-bold tracking-widest">
                via {{ payment.payment_gateway }}
              </div>
            </td>

            <td class="px-6 py-4">
              <span 
                class="inline-flex items-center px-2.5 py-0.5 rounded-full border text-[10px] font-bold uppercase"
                :class="getStatusStyles(payment.status)"
              >
                {{ payment.status }}
              </span>
            </td>

            <td class="px-6 py-4">
              <div 
                class="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full border text-[10px] font-bold uppercase"
                :class="getEscrowStyles(payment.escrow_status).class"
              >
                <component :is="getEscrowStyles(payment.escrow_status).icon" :size="10" />
                {{ payment.escrow_status }}
              </div>
            </td>

            <td class="px-6 py-4">
              <div class="flex items-center gap-2 text-xs text-white/40 font-medium">
                <Calendar :size="12" />
                {{ new Date(payment.paid_at).toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' }) }}
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
          class="px-4 py-2 text-[10px] font-bold uppercase border border-white/10 rounded-lg text-white/40 disabled:opacity-10 transition-all hover:bg-white/5"
        >
          Prev
        </button>
        <button 
          @click="emit('changePage', currentPage + 1)" 
          :disabled="currentPage >= totalPages"
          class="px-4 py-2 text-[10px] font-bold uppercase border border-white/10 rounded-lg text-white/40 disabled:opacity-10 transition-all hover:bg-white/5"
        >
          Next
        </button>
      </div>
    </div>
  </div>
</template>