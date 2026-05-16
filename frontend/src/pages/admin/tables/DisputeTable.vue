<script setup>
import { 
  AlertTriangle, Calendar, ClipboardList, X,
  User, CheckCircle2, Clock, Copy, Check, MessageSquare, ShieldCheck, Loader2
} from 'lucide-vue-next';
import { ref } from 'vue';
import { resolveDispute } from '../../../api/api';

const props = defineProps({
  disputes: {
    type: Array,
    required: true,
    default: () => []
  },
  currentPage: Number,
  totalPages: Number
});

const emit = defineEmits(['changePage', 'refresh']);

// UI States
const copiedId = ref(null);
const isModalOpen = ref(false);
const isSubmitting = ref(false);

// Form States
const selectedDispute = ref(null);
const resolutionAction = ref('auto');

const copyToClipboard = async (text, event) => {
  event.stopPropagation();
  try {
    await navigator.clipboard.writeText(text);
    copiedId.value = text;
    setTimeout(() => { copiedId.value = null; }, 2000);
  } catch (err) {
    console.error('Failed to copy!', err);
  }
};

const openResolveModal = (dispute) => {
  if (dispute.status !== 'pending') return;
  selectedDispute.value = dispute;
  resolutionAction.value = 'auto';
  isModalOpen.value = true;
};

const handleSubmit = async () => {
  if (!selectedDispute.value) return;
  
  isSubmitting.value = true;
  
  try {
    const payload = {
      disputeId: selectedDispute.value.id,
      body: {
        action: resolutionAction.value
      }
    };

    const response = await resolveDispute(payload);
    console.log("Resolution successful:", response);

    // Close modal and reset state
    isModalOpen.value = false;
    selectedDispute.value = null;

    // Trigger the refetch in the parent component
    emit('refresh'); 
    
  } catch (err) {
    console.error('Failed to resolve dispute:', err.response?.data?.detail || err.message);
  } finally {
    isSubmitting.value = false;
  }
};

const getStatusStyles = (status) => {
  switch (status) {
    case 'resolved':
      return 'bg-emerald-500/10 border-emerald-500/20 text-emerald-400';
    case 'pending':
      return 'bg-amber-500/10 border-amber-500/20 text-amber-400';
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
            <th class="px-6 py-4">Dispute Details</th>
            <th class="px-6 py-4">Reason</th>
            <th class="px-6 py-4">Related IDs</th>
            <th class="px-6 py-4">Status</th>
            <th class="px-6 py-4">Filed On</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-white/5">
          <tr 
            v-for="dispute in disputes" 
            :key="dispute.id" 
            @click="openResolveModal(dispute)"
            class="hover:bg-white/2 transition-colors group cursor-pointer"
          >
            <td class="px-6 py-4">
              <div class="flex items-center gap-3">
                <div class="w-9 h-9 rounded-lg bg-amber-500/10 border border-amber-500/20 flex items-center justify-center text-amber-500 group-hover:scale-110 transition-transform">
                  <AlertTriangle :size="18" />
                </div>
                <div>
                  <div class="font-bold text-[#f0ede4] text-xs uppercase tracking-tight">Active Dispute</div>
                  <div class="text-[12px] text-white/30 font-mono flex items-center gap-1">
                    #{{ dispute.id.slice(0, 8) }}
                    <button @click="copyToClipboard(dispute.id, $event)" class="hover:text-[#7bc95a]">
                      <Check v-if="copiedId === dispute.id" :size="10" />
                      <Copy v-else :size="10" />
                    </button>
                  </div>
                </div>
              </div>
            </td>

            <td class="px-6 py-4">
              <div class="flex items-start gap-2 max-w-62.5">
                <MessageSquare :size="14" class="text-white/20 mt-0.5 shrink-0" />
                <p class="text-xs text-white/60 leading-relaxed line-clamp-2">
                  "{{ dispute.reason }}"
                </p>
              </div>
            </td>

            <td class="px-6 py-4 text-[10px]">
              <div class="space-y-1">
                <div class="flex items-center gap-2 text-white/40">
                  <ClipboardList :size="10" /> 
                  Order: <span class="text-white/60 font-mono">{{ dispute.order_id}}</span>
                </div>
                <div class="flex items-center gap-2 text-white/40">
                  <User :size="10" /> 
                  Buyer: <span class="text-white/60 font-mono">{{ dispute.buyer_id }}</span>
                </div>
              </div>
            </td>

            <td class="px-6 py-4">
              <span 
                class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full border text-[9px] font-black uppercase tracking-wider"
                :class="getStatusStyles(dispute.status)"
              >
                <Clock v-if="dispute.status === 'pending'" :size="10" />
                <CheckCircle2 v-else :size="10" />
                {{ dispute.status }}
              </span>
            </td>

            <td class="px-6 py-4">
              <div class="flex items-center gap-2 text-xs text-white/40 font-medium">
                <Calendar :size="12" />
                {{ new Date(dispute.created_at).toLocaleDateString('en-GB', { day: '2-digit', month: 'short' }) }}
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <div v-if="isModalOpen" class="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div class="absolute inset-0 bg-black/80 backdrop-blur-sm" @click="isModalOpen = false"></div>
      
      <div class="relative w-full max-w-md bg-[#121212] border border-white/10 rounded-3xl overflow-hidden shadow-2xl">
        <div class="p-6 border-b border-white/5 flex justify-between items-center">
          <h3 class="text-lg font-bold text-white flex items-center gap-2">
            <ShieldCheck class="text-[#7bc95a]" :size="20" />
            Resolve Dispute
          </h3>
          <button @click="isModalOpen = false" class="text-white/20 hover:text-white transition-colors">
            <X :size="20" />
          </button>
        </div>

        <div class="p-8 space-y-6">
          <div class="bg-white/5 p-4 rounded-2xl border border-white/5">
            <p class="text-[10px] font-bold text-white/30 uppercase tracking-widest mb-2">Complainant Reason</p>
            <p class="text-sm text-white/70 italic leading-relaxed">"{{ selectedDispute?.reason }}"</p>
          </div>

          <div class="space-y-3">
            <label class="text-[10px] font-bold text-white/30 uppercase tracking-widest">Select Resolution Action</label>
            <select 
              v-model="resolutionAction"
              class="w-full bg-white/5 border border-white/10 rounded-xl py-4 px-4 text-white outline-none focus:border-[#5cb83a]/50 appearance-none cursor-pointer"
            >
              <option class="text-black" value="auto">System Default (Auto)</option>
              <option class="text-black" value="refund_buyer">Refund Buyer</option>
              <option class="text-black" value="release_farmer">Release Funds to Farmer</option>
            </select>
          </div>

          <button 
            @click="handleSubmit"
            :disabled="isSubmitting"
            class="w-full bg-[#2d7a18] hover:bg-[#3a9e20] text-white py-4 rounded-xl font-bold flex items-center justify-center gap-2 transition-all active:scale-[0.98] disabled:opacity-50"
          >
            <Loader2 v-if="isSubmitting" class="animate-spin" :size="20" />
            <CheckCircle2 v-else :size="20" />
            Submit Resolution
          </button>
        </div>
      </div>
    </div>

    <div class="flex items-center justify-between px-2">
      <p class="text-[10px] text-white/30 font-bold uppercase tracking-widest">
        Showing Page {{ currentPage }} of {{ totalPages }}
      </p>
      <div class="flex gap-2">
        <button @click="emit('changePage', currentPage - 1)" :disabled="currentPage <= 1"
          class="px-4 py-2 text-[10px] font-bold uppercase border border-white/10 rounded-lg text-white/40 disabled:opacity-10 hover:bg-white/5">
          Prev
        </button>
        <button @click="emit('changePage', currentPage + 1)" :disabled="currentPage >= totalPages"
          class="px-4 py-2 text-[10px] font-bold uppercase border border-white/10 rounded-lg text-white/40 disabled:opacity-10 hover:bg-white/5">
          Next
        </button>
      </div>
    </div>
  </div>
</template>