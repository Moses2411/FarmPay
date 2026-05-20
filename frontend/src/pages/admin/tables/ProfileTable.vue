<script setup>
import { 
  MapPin, Landmark, Star, Copy, Check, 
  Leaf, TrendingUp, ShieldCheck 
} from 'lucide-vue-next';
import { ref } from 'vue';

const props = defineProps({
  farmers: {
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
</script>

<template>
  <div class="w-full space-y-4">
    <div class="w-full overflow-x-auto rounded-2xl border border-white/10 bg-white/5 backdrop-blur-sm">
      <table class="w-full text-left border-collapse">
        <thead>
          <tr class="border-b border-white/10 bg-white/5 text-[10px] font-bold uppercase tracking-widest text-[#7bc95a]">
            <th class="px-6 py-4">Business & Location</th>
            <th class="px-6 py-4">Verification (NIN)</th>
            <th class="px-6 py-4">Banking Details</th>
            <th class="px-6 py-4">Joined Date</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-white/5">
          <tr v-for="farmer in farmers" :key="farmer.id" class="hover:bg-white/2 transition-colors group">
            <td class="px-6 py-4">
              <div class="flex items-center gap-3">
                <div class="w-9 h-9 rounded-xl bg-[#5cb83a]/10 border border-[#5cb83a]/20 flex items-center justify-center text-[#7bc95a]">
                  <Leaf :size="18" />
                </div>
                <div>
                  <div class="font-bold text-[#f0ede4] text-sm">{{ farmer.business_name || 'Unnamed Farm' }}</div>
                  <div class="flex items-center gap-1 text-[10px] text-white/30 capitalize">
                    <MapPin :size="10" />
                    {{ farmer.location?.replace('_', ' ') }}
                  </div>
                </div>
              </div>
            </td>

            <td class="px-6 py-4">
              <div class="flex flex-col gap-1">
                <span class="text-xs text-white/50 font-mono tracking-wider">NIN: {{ farmer.nin }}</span>
                <div class="flex items-center gap-1 text-[9px] text-emerald-400 font-bold uppercase">
                  <ShieldCheck :size="10" /> Verified Identity
                </div>
              </div>
            </td>

            <td class="px-6 py-4">
              <div class="flex flex-col gap-0.5">
                <div class="flex items-center gap-1.5 text-xs text-white/70 font-semibold">
                  <Landmark :size="12" class="text-white/20" />
                  {{ farmer.bank_name }}
                </div>
                <div class="text-[11px] text-white/30 font-mono tracking-tighter">
                  {{ farmer.account_number }}
                </div>
              </div>
            </td>

            <td class="px-6 py-4 text-xs text-white/40 font-medium">
              {{ new Date(farmer.created_at).toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' }) }}
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <div class="flex items-center justify-between px-2">
      <p class="text-[10px] text-white/30 font-bold uppercase tracking-widest">
Showing Page {{ currentPage }} of {{ totalPages }}      </p>
      <div class="flex gap-2">
        <button @click="emit('changePage', currentPage - 1)" :disabled="currentPage <= 1"
          class="px-4 py-2 text-[10px] font-bold uppercase border border-white/10 rounded-lg text-white/40 disabled:opacity-10 hover:bg-white/5 transition-all">
          Prev
        </button>
        <button @click="emit('changePage', currentPage + 1)" :disabled="currentPage >= totalPages"
          class="px-4 py-2 text-[10px] font-bold uppercase border border-white/10 rounded-lg text-white/40 disabled:opacity-10 hover:bg-white/5 transition-all">
          Next
        </button>
      </div>
    </div>
  </div>
</template>