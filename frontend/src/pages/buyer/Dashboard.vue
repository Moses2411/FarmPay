<script setup>
import { ref, onMounted, computed } from 'vue';
import { useRouter } from 'vue-router';
import { useAuthStore } from '../../stores/auth';
import api from '@/api/api';
import { 
  Package, ShieldCheck, Clock, CheckCircle2, 
  MapPin, Copy, Loader2, Inbox, LayoutDashboard,
  ShoppingBag, LogOut, Bell, RotateCw, 
  AlertCircle, X, Upload, Trash2, ImageIcon
} from 'lucide-vue-next';

const router = useRouter();
const auth = useAuthStore();
const orders = ref([]);
const isLoading = ref(true);

// --- Dispute Modal State ---
const isDisputeModalOpen = ref(false);
const disputeOrder = ref(null);
const disputeReason = ref('');
const disputeImages = ref([]); // Stores Base64 strings
const isSubmittingDispute = ref(false);

// User Profile
const user = ref({
  name: auth.user?.fullName?.split(' ')[0] || 'User',
  email: auth.user?.email,
  avatar: null,
  role: auth.user?.role || 'Buyer'
});

const fetchOrders = async () => {
  isLoading.value = true;
  try {
    const response = await api.get('/orders/my-orders'); 
    orders.value = response.data || response;
    console.log(orders.value)
  } catch (err) {
    console.error("Error fetching orders:", err);
  } finally {
    isLoading.value = false;
  }
};

// --- Dispute Logic ---
const openDisputeModal = (order) => {
  disputeOrder.value = order;
  disputeReason.value = '';
  disputeImages.value = [];
  isDisputeModalOpen.value = true;
};

const handleImageUpload = (event) => {
  const files = Array.from(event.target.files);
  files.forEach(file => {
    const reader = new FileReader();
    reader.onload = (e) => {
      disputeImages.value.push(e.target.result); // Base64 string
    };
    reader.readAsDataURL(file);
  });
};

const removeImage = (index) => {
  disputeImages.value.splice(index, 1);
};

const submitDispute = async () => {
  if (!disputeReason.value || disputeImages.value.length === 0) return;

  isSubmittingDispute.value = true;
  try {
    // Payload as per Swagger UI: order_id, reason, images (array of strings)
    await api.post('/disputes/create', {
      order_id: disputeOrder.value.id,
      reason: disputeReason.value,
      images: disputeImages.value
    });

    alert("Dispute submitted. Our team will review the evidence.");
    isDisputeModalOpen.value = false;
    fetchOrders(); // Refresh to show disputed status
  } catch (err) {
    alert(err.response?.data?.message || "Failed to submit dispute.");
  } finally {
    isSubmittingDispute.value = false;
  }
};

const handleLogout = () => {
  auth.logout();
  router.push('/login');
};

const copyOTP = (otp) => {
  if (!otp) return;
  navigator.clipboard.writeText(otp.replace(/\s/g, ''));
  alert("Release Code copied!");
};

onMounted(fetchOrders);

// Stats Computed Logic
const totalSpent = computed(() => {
  return orders.value
    .filter(o => o.status === 'completed')
    .reduce((sum, o) => sum + (Number(o.total_amount) || 0), 0);
});

const inEscrow = computed(() => {
  return orders.value
    .filter(o => o.escrow_status === 'held')
    .reduce((sum, o) => sum + (Number(o.total_amount) || 0), 0);
});
</script>

<template>
  <div class="flex min-h-screen bg-[#061209] text-[#f0ede4]">
    
    <aside class="w-64 border-r border-white/5 bg-[#081a0c] hidden md:flex flex-col p-6 sticky top-0 h-screen">
      <div class="mb-10 flex items-center gap-2 px-2 cursor-pointer" @click="router.push('/')">
        <div class="w-8 h-8 bg-[#5cb83a] rounded-lg flex items-center justify-center">
          <ShieldCheck class="text-[#061209]" :size="20" />
        </div>
        <span class="font-serif text-xl font-bold tracking-tight">FarmPay</span>
      </div>

      <nav class="flex-1 space-y-2">
        <button class="w-full flex items-center gap-3 px-4 py-3 rounded-2xl bg-[#5cb83a]/10 text-[#5cb83a] font-medium">
          <LayoutDashboard :size="20" /> Dashboard
        </button>
        <button @click="router.push('/marketplace')" class="w-full flex items-center gap-3 px-4 py-3 rounded-2xl hover:bg-white/5 text-white/40 hover:text-white transition-all">
          <ShoppingBag :size="20" /> Marketplace
        </button>
      </nav>

      <div class="mt-auto pt-6 border-t border-white/5">
        <div class="flex items-center gap-3 mb-4 px-2">
          <div class="w-10 h-10 rounded-full bg-[#5cb83a]/20 border border-[#5cb83a]/30 flex items-center justify-center text-[#5cb83a] font-bold">
            {{ user.name.charAt(0) }}
          </div>
          <div class="overflow-hidden">
            <p class="text-sm font-bold truncate">{{ user.name }}</p>
            <p class="text-[10px] text-white/30 uppercase tracking-widest">{{ user.role }}</p>
          </div>
        </div>
        <button @click="handleLogout" class="w-full flex items-center gap-3 px-4 py-3 rounded-2xl text-red-400 hover:bg-red-400/10 transition-all text-sm font-medium">
          <LogOut :size="18" /> Logout
        </button>
      </div>
    </aside>

    <main class="flex-1 p-6 md:p-10 overflow-y-auto">
      <div class="max-w-5xl mx-auto">
        
        <header class="mb-10 flex justify-between items-center">
          <div>
            <h1 class="text-3xl font-serif">Buyer Terminal</h1>
            <p class="text-white/40 text-sm italic">Secure produce acquisition & escrow management.</p>
          </div>
          <div class="flex items-center gap-3">
            <button @click="fetchOrders" class="p-3 rounded-full bg-white/5 border border-white/10 hover:border-[#5cb83a] transition-all">
              <RotateCw :size="18" :class="{ 'animate-spin': isLoading }" />
            </button>
          </div>
        </header>

        <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12">
          <div class="bg-white/5 border border-white/10 p-6 rounded-[2.5rem]">
            <p class="text-[10px] uppercase tracking-widest text-white/30 font-bold mb-2">Total Settled</p>
            <p class="text-3xl font-serif">₦{{ totalSpent.toLocaleString() }}</p>
          </div>
          <div class="bg-[#5cb83a]/10 border border-[#5cb83a]/20 p-6 rounded-[2.5rem] relative overflow-hidden">
            <ShieldCheck class="absolute -right-4 -bottom-4 text-[#5cb83a]/5" :size="100" />
            <p class="text-[10px] uppercase tracking-widest text-[#5cb83a] font-bold mb-2">Active Escrow</p>
            <p class="text-3xl font-serif">₦{{ inEscrow.toLocaleString() }}</p>
          </div>
          <div class="bg-white/5 border border-white/10 p-6 rounded-[2.5rem]">
            <p class="text-[10px] uppercase tracking-widest text-white/30 font-bold mb-2">In Transit</p>
            <p class="text-3xl font-serif">{{ orders.filter(o => o.delivery_status === 'transit').length }}</p>
          </div>
        </div>

        <section class="space-y-6">
          <h3 class="font-bold text-xs uppercase tracking-[0.2em] text-white/40 px-2">Order History</h3>

          <div v-if="isLoading" class="flex flex-col items-center justify-center py-20">
            <Loader2 class="animate-spin text-[#5cb83a]" :size="32" />
          </div>

          <div v-else-if="orders.length === 0" class="text-center py-20 bg-white/2 rounded-[2.5rem] border border-white/5">
            <Inbox :size="40" class="mx-auto mb-4 text-white/10" />
            <p class="text-white/40">No orders found.</p>
          </div>

          <div v-else v-for="order in orders" :key="order.id" 
               class="bg-[#0d2010] border border-white/10 rounded-[2.5rem] p-6 flex flex-col md:flex-row items-center gap-6 transition-all hover:bg-[#112814]">
            
            <div class="w-16 h-16 rounded-2xl bg-black/20 border border-white/5 flex items-center justify-center shrink-0">
              <Package class="text-[#5cb83a]/40" :size="28" />
            </div>

            <div class="flex-1">
              <div class="flex items-center gap-2 mb-2">
                <span class="text-[9px] font-mono text-white/20 uppercase">#{{ order.id.slice(-8) }}</span>
                <h4 class="font-bold text-lg leading-tight">{{ order.delivery_location }} Delivery</h4>
              </div>
              
              <div class="flex gap-4 items-center">
                <div v-if="order.delivery_status === 'disputed'" class="text-red-400 font-bold text-[10px] uppercase flex items-center gap-1">
                  <AlertCircle :size="12" /> Disputed
                </div>
                <div v-else-if="order.status === 'completed'" class="text-[#5cb83a] font-bold text-[10px] uppercase flex items-center gap-1">
                  <CheckCircle2 :size="12" /> Success
                </div>
                <div v-else class="text-white/40 font-bold text-[10px] uppercase flex items-center gap-1">
                  <Clock :size="12" /> {{ order.delivery_status }}
                </div>
              </div>
            </div>

            <div v-if="order.status !== 'completed' && order.delivery_status !== 'disputed' && order.otp_code" 
                 class="bg-black/40 border border-[#5cb83a]/20 px-6 py-4 rounded-3xl text-center">
              <span class="text-[8px] uppercase tracking-widest text-[#5cb83a] font-bold block mb-1">Release Code</span>
              <div class="flex items-center gap-3">
                <span class="text-xl font-mono font-bold text-[#f0ede4]">{{ order.otp_code }}</span>
                <button @click="copyOTP(order.otp_code)" class="text-white/20 hover:text-[#5cb83a]"><Copy :size="14" /></button>
              </div>
            </div>

            <div v-if="order.status !== 'completed' && order.delivery_status !== 'disputed'">
              <button @click="openDisputeModal(order)" class="bg-red-500/10 text-red-400 border border-red-500/20 px-4 py-2 rounded-xl text-[9px] font-bold uppercase tracking-widest hover:bg-red-500/20 transition-all">
                Dispute
              </button>
            </div>

            <div class="text-right shrink-0">
               <span class="text-[9px] text-white/20 block uppercase font-bold mb-1">Total Amount</span>
               <span class="text-xl font-serif">₦{{ (order.total_amount || 0).toLocaleString() }}</span>
            </div>
          </div>
        </section>
      </div>
    </main>

    <div v-if="isDisputeModalOpen" class="fixed inset-0 z-100 flex items-center justify-center p-4 bg-[#061209]/95 backdrop-blur-md">
      <div class="bg-[#0d2010] border border-white/10 w-full max-w-lg rounded-[3rem] p-8 shadow-2xl">
        
        <div class="flex justify-between items-center mb-8">
          <h2 class="text-2xl font-serif">Raise Dispute</h2>
          <button @click="isDisputeModalOpen = false" class="text-white/20 hover:text-white"><X :size="24" /></button>
        </div>

        <div class="space-y-6">
          <div>
            <label class="text-[10px] uppercase tracking-widest text-white/30 font-bold mb-2 block">Issue Description</label>
            <textarea v-model="disputeReason" rows="3" placeholder="Describe what's wrong with the produce..." 
                      class="w-full bg-white/5 border border-white/10 rounded-2xl p-4 text-sm outline-none focus:border-red-500/50 transition-all"></textarea>
          </div>

          <div>
            <label class="text-[10px] uppercase tracking-widest text-white/30 font-bold mb-2 block">Photo Evidence (Max 3)</label>
            <div class="grid grid-cols-3 gap-3">
              <div v-for="(img, idx) in disputeImages" :key="idx" class="relative aspect-square rounded-xl overflow-hidden border border-white/10">
                <img :src="img" class="w-full h-full object-cover" />
                <button @click="removeImage(idx)" class="absolute top-1 right-1 bg-red-500 p-1 rounded-lg"><Trash2 :size="12" /></button>
              </div>
              <label v-if="disputeImages.length < 3" class="aspect-square rounded-xl border-2 border-dashed border-white/10 flex flex-col items-center justify-center gap-1 cursor-pointer hover:bg-white/5 transition-all">
                <Upload class="text-[#5cb83a]" :size="18" />
                <span class="text-[8px] font-bold uppercase opacity-40">Add</span>
                <input type="file" multiple accept="image/*" class="hidden" @change="handleImageUpload" />
              </label>
            </div>
          </div>

          <button @click="submitDispute" :disabled="isSubmittingDispute || !disputeReason || disputeImages.length === 0"
                  class="w-full bg-red-500 text-white py-4 rounded-2xl font-bold text-xs uppercase tracking-widest flex items-center justify-center gap-2 disabled:opacity-20 transition-all">
            <Loader2 v-if="isSubmittingDispute" class="animate-spin" :size="18" />
            Submit Dispute to Escrow
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.no-scrollbar::-webkit-scrollbar { display: none; }
</style>