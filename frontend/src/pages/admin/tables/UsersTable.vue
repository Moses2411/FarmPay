<script setup>
import { ref } from 'vue';
import { 
  Mail, Phone, User, Copy, Check, 
  ShieldCheck, ShoppingBag, Truck, Leaf,
  Loader2, CheckCircle
} from 'lucide-vue-next';

const props = defineProps({
  users: {
    type: Array,
    required: true,
    default: () => []
  },
  currentPage: Number,
  totalPages: Number
});

const emit = defineEmits(['changePage', 'verifyUser']);

const copiedId = ref(null);
const verifyingId = ref(null);

const copyToClipboard = async (id) => {
  try {
    await navigator.clipboard.writeText(id);
    copiedId.value = id;
    setTimeout(() => { copiedId.value = null; }, 2000);
  } catch (err) {
    console.error('Failed to copy!', err);
  }
};

const verifyUser = async (userId) => {
  verifyingId.value = userId;
  emit('verifyUser', userId);
  setTimeout(() => { verifyingId.value = null; }, 3000);
};

const getRoleStyles = (role) => {
  switch (role) {
    case 'admin':
      return { bg: 'bg-purple-500/10', border: 'border-purple-500/20', text: 'text-purple-400', icon: ShieldCheck };
    case 'dispatch_rider':
      return { bg: 'bg-blue-500/10', border: 'border-blue-500/20', text: 'text-blue-400', icon: Truck };
    case 'farmer':
      return { bg: 'bg-emerald-500/10', border: 'border-emerald-500/20', text: 'text-emerald-400', icon: Leaf };
    case 'buyer':
      return { bg: 'bg-orange-500/10', border: 'border-orange-500/20', text: 'text-orange-400', icon: ShoppingBag };
    default:
      return { bg: 'bg-white/10', border: 'border-white/20', text: 'text-white/60', icon: User };
  }
};

const formatDate = (dateStr) => {
  if (!dateStr) return 'N/A';
  return new Date(dateStr).toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' });
};
</script>

<template>
  <div class="w-full space-y-4">
    <div class="w-full overflow-x-auto rounded-2xl border border-white/10 bg-white/5 backdrop-blur-sm">
      <table class="w-full text-left border-collapse">
        <thead>
          <tr class="border-b border-white/10 bg-white/5 text-[10px] font-bold uppercase tracking-widest text-[#7bc95a]">
            <th class="px-6 py-4">User Details</th>
            <th class="px-6 py-4">User ID</th>
            <th class="px-6 py-4">Contact Info</th>
            <th class="px-6 py-4">Role</th>
            <th class="px-6 py-4">Status</th>
            <th class="px-6 py-4">Joined Date</th>
            <th class="px-6 py-4">Actions</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-white/5">
          <tr v-for="user in users" :key="user.id" class="hover:bg-white/2 transition-colors group">
            <td class="px-6 py-4">
              <div class="flex items-center gap-3">
                <div class="w-9 h-9 rounded-full bg-white/5 border border-white/10 flex items-center justify-center text-white/40">
                  <User :size="18" />
                </div>
                <div>
                  <div class="font-semibold text-[#f0ede4] capitalize text-sm">{{ user.full_name }}</div>
                  <div v-if="user.is_verified" class="text-[9px] text-[#7bc95a] uppercase font-bold tracking-tighter flex items-center gap-1">
                    <CheckCircle :size="10" /> Verified
                  </div>
                </div>
              </div>
            </td>

            <td class="px-6 py-4">
              <div class="flex items-center gap-2">
                <span class="text-xs text-white/30 font-mono">#{{ user.id?.slice(0, 8) }}</span>
                <button @click="copyToClipboard(user.id)" class="text-white/10 hover:text-[#7bc95a] transition-colors">
                  <Check v-if="copiedId === user.id" :size="12" class="text-[#7bc95a]" />
                  <Copy v-else :size="12" />
                </button>
              </div>
            </td>

            <td class="px-6 py-4">
              <div class="space-y-1 text-xs text-white/50">
                <div class="flex items-center gap-2"><Mail :size="12" />{{ user.email }}</div>
                <div class="flex items-center gap-2"><Phone :size="12" />{{ user.phone_number }}</div>
              </div>
            </td>

            <td class="px-6 py-4">
              <span 
                class="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full border text-[10px] font-bold uppercase"
                :class="[getRoleStyles(user.role).bg, getRoleStyles(user.role).border, getRoleStyles(user.role).text]"
              >
                <component :is="getRoleStyles(user.role).icon" :size="10" />
                {{ user.role?.replace('_', ' ') }}
              </span>
            </td>

            <td class="px-6 py-4">
              <span 
                v-if="user.is_verified"
                class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-[#5cb83a]/10 text-[#5cb83a] text-[9px] font-bold uppercase"
              >
                <CheckCircle :size="10" /> Active
              </span>
              <span 
                v-else
                class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-amber-500/10 text-amber-500 text-[9px] font-bold uppercase"
              >
                Pending
              </span>
            </td>

            <td class="px-6 py-4 text-xs text-white/40 font-medium">
              {{ formatDate(user.created_at) }}
            </td>

            <td class="px-6 py-4">
              <button 
                v-if="!user.is_verified"
                @click="verifyUser(user.id)"
                :disabled="verifyingId === user.id"
                class="px-3 py-1.5 rounded-lg bg-[#5cb83a]/10 text-[#5cb83a] text-[9px] font-bold uppercase tracking-wider hover:bg-[#5cb83a]/20 transition-all flex items-center gap-1.5"
              >
                <Loader2 v-if="verifyingId === user.id" class="animate-spin" :size="12" />
                <CheckCircle v-else :size="12" />
                Verify
              </button>
              <span v-else class="text-[9px] text-white/20 uppercase">-</span>
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
          class="px-4 py-2 text-[10px] font-bold uppercase border border-white/10 rounded-lg text-white/40 disabled:opacity-10"
        >
          Prev
        </button>
        <button 
          @click="emit('changePage', currentPage + 1)" 
          :disabled="currentPage >= totalPages"
          class="px-4 py-2 text-[10px] font-bold uppercase border border-white/10 rounded-lg text-white/40 disabled:opacity-10"
        >
          Next
        </button>
      </div>
    </div>
  </div>
</template>