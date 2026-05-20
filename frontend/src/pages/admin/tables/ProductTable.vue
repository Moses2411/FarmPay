<script setup>
import { 
  Package, Tag, ShoppingCart, Info, 
  CheckCircle2, Clock, AlertCircle, Copy, Check 
} from 'lucide-vue-next';
import { ref } from 'vue';

const props = defineProps({
  products: {
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

const getScanStatusStyles = (status) => {
  switch (status) {
    case 'scanned':
    case 'approved':
      return 'bg-emerald-500/10 border-emerald-500/20 text-emerald-400';
    case 'pending':
      return 'bg-orange-500/10 border-orange-500/20 text-orange-400';
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
            <th class="px-6 py-4">Product Info</th>
            <th class="px-6 py-4">Inventory & Price</th>
            <th class="px-6 py-4">Quality Scan</th>
            <th class="px-6 py-4">Approval</th>
            <th class="px-6 py-4">Listing Date</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-white/5">
          <tr v-for="product in products" :key="product.id" class="hover:bg-white/2 transition-colors group">
            <td class="px-6 py-4">
              <div class="flex items-start gap-3">
                <div class="w-10 h-10 rounded-xl bg-white/5 border border-white/10 flex items-center justify-center text-white/20">
                  <Package :size="20" />
                </div>
                <div class="flex flex-col">
                  <span class="font-bold text-[#f0ede4] capitalize text-sm">{{ product.name }}</span>
                  <span class="text-[10px] text-white/30 truncate max-w-45 italic">
                    {{ product.description || 'No description provided' }}
                  </span>
                  <div class="flex items-center gap-2 mt-1">
                    <span class="text-[9px] font-mono text-white/20">{{ product.id.slice(0, 8) }}</span>
                    <button @click="copyToClipboard(product.id)" class="text-white/10 hover:text-[#7bc95a]">
                      <Check v-if="copiedId === product.id" :size="10" class="text-[#7bc95a]" />
                      <Copy v-else :size="10" />
                    </button>
                  </div>
                </div>
              </div>
            </td>

            <td class="px-6 py-4">
              <div class="flex flex-col gap-1">
                <div class="text-sm font-bold text-white">{{ formatCurrency(product.price) }}</div>
                <div class="flex items-center gap-1.5">
                  <ShoppingCart :size="10" class="text-[#7bc95a]" />
                  <span class="text-[11px] text-white/50 font-medium">
                    {{ product.available_quantity }} {{ product.unit }} left
                  </span>
                </div>
              </div>
            </td>

            <td class="px-6 py-4">
              <span 
                class="inline-flex items-center px-2.5 py-1 rounded-full border text-[9px] font-black uppercase tracking-wider"
                :class="getScanStatusStyles(product.scan_status)"
              >
                {{ product.scan_status }}
              </span>
            </td>

            <td class="px-6 py-4">
              <div v-if="product.is_approved" class="flex items-center gap-1.5 text-emerald-400 text-[10px] font-bold uppercase">
                <CheckCircle2 :size="14" />
                Live on Store
              </div>
              <div v-else class="flex items-center gap-1.5 text-orange-400/60 text-[10px] font-bold uppercase">
                <Clock :size="14" />
                Awaiting Review
              </div>
            </td>

            <td class="px-6 py-4 text-[11px] text-white/40 font-medium">
              {{ new Date(product.created_at).toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' }) }}
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <div class="flex items-center justify-between px-2">
      <p class="text-[10px] text-white/30 font-bold uppercase tracking-widest">
Showing Page {{ currentPage }} of {{ totalPages }}      </p>
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