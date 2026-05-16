<script setup>
import { 
  Mail, Phone, User, Trash2, Edit, 
  Copy, Check 
} from 'lucide-vue-next';
import { ref } from 'vue';

const props = defineProps({
  riders: {
    type: Array,
    required: true,
    default: () => []
  },
  currentPage: Number,
  totalPages: Number
});

const emit = defineEmits(['edit', 'delete', 'changePage']);

const copiedId = ref(null);

const copyToClipboard = async (id) => {
  try {
    await navigator.clipboard.writeText(id);
    copiedId.value = id;
    setTimeout(() => {
      copiedId.value = null;
    }, 2000);
  } catch (err) {
    console.error('Failed to copy!', err);
  }
};
</script>

<template>
  <div class="w-full space-y-4">
    <div class="w-full overflow-x-auto rounded-2xl border border-white/10 bg-white/5 backdrop-blur-sm">
      <table class="w-full text-left border-collapse">
        <thead>
          <tr class="border-b border-white/10 bg-white/5">
            <th class="px-6 py-4 text-xs font-bold uppercase tracking-widest text-[#7bc95a]">Rider Details</th>
            <th class="px-6 py-4 text-xs font-bold uppercase tracking-widest text-[#7bc95a]">Rider ID</th>
            <th class="px-6 py-4 text-xs font-bold uppercase tracking-widest text-[#7bc95a]">Contact Info</th>
            <th class="px-6 py-4 text-xs font-bold uppercase tracking-widest text-[#7bc95a]">Status</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-white/5">
          <tr 
            v-for="rider in riders" 
            :key="rider.id" 
            class="hover:bg-white/2 transition-colors group"
          >
            <td class="px-6 py-4">
              <div class="flex items-center gap-3">
                <div class="w-10 h-10 rounded-full bg-[#2d7a18]/20 border border-[#5cb83a]/20 flex items-center justify-center text-[#7bc95a]">
                  <User :size="20" />
                </div>
                <div>
                  <div class="font-semibold text-[#f0ede4] capitalize text-sm">{{ rider.full_name }}</div>
                  <div class="text-[10px] text-white/40 uppercase font-bold tracking-tight">Verified Rider</div>
                </div>
              </div>
            </td>

            <td class="px-6 py-4">
              <div class="flex items-center gap-2">
                <span class="text-sm text-white/40 font-mono">#{{ rider.id?.slice(0, 8) }}</span>
                <button 
                  @click="copyToClipboard(rider.id)" 
                  class="hover:text-[#7bc95a] transition-colors text-white/10 group-hover:text-white/30"
                  title="Copy Rider ID"
                >
                  <Check v-if="copiedId === rider.id" :size="14" class="text-[#7bc95a]" />
                  <Copy v-else :size="14" />
                </button>
              </div>
            </td>

            <td class="px-6 py-4">
              <div class="space-y-1">
                <div class="flex items-center gap-2 text-xs text-white/60">
                  <Mail :size="12" class="text-[#5cb83a]/50" />
                  {{ rider.email }}
                </div>
                <div class="flex items-center gap-2 text-xs text-white/60">
                  <Phone :size="12" class="text-[#5cb83a]/50" />
                  {{ rider.phone_number }}
                </div>
              </div>
            </td>

            <td class="px-6 py-4">
              <span class="inline-flex items-center px-2.5 py-0.5 rounded-full bg-[#5cb83a]/10 border border-[#5cb83a]/20 text-[#7bc95a] text-[10px] font-bold uppercase">
                Available
              </span>
            </td>

          </tr>

          <tr v-if="riders.length === 0">
            <td colspan="5" class="px-6 py-12 text-center text-white/20 italic font-medium">
              No dispatch riders found in the system.
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <div class="flex items-center justify-between px-2">
      <p class="text-[10px] text-white/30 font-bold uppercase tracking-wider">
        Showing Page {{ currentPage }} of {{ totalPages }}
      </p>
      <div class="flex gap-2">
        <button 
          @click="emit('changePage', currentPage - 1)"
          :disabled="currentPage <= 1"
          class="px-4 py-2 text-[10px] font-bold uppercase border border-white/10 rounded-lg text-white/40 hover:bg-white/5 disabled:opacity-10 transition-all"
        >
          Previous
        </button>
        <button 
          @click="emit('changePage', currentPage + 1)"
          :disabled="currentPage >= totalPages"
          class="px-4 py-2 text-[10px] font-bold uppercase border border-white/10 rounded-lg text-white/40 hover:bg-white/5 disabled:opacity-10 transition-all"
        >
          Next
        </button>
      </div>
    </div>
  </div>
</template>