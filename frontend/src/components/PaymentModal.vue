<script setup>
import { ref, computed } from 'vue';
import api from '@/api/api';
import { Minus, Plus, ShieldCheck, Lock, X, Loader2, MapPin } from 'lucide-vue-next';

const props = defineProps(['product', 'isOpen']);
const emit = defineEmits(['close', 'payment-success']);

const isProcessing = ref(false);
const quantity = ref(1);
const selectedLocation = ref(null);

const dropOffPoints = [
  { id: 'dp1', name: 'kaduna_south', fee: 1500 },
  { id: 'dp2', name: 'kaduna_north', fee: 2000 },
  { id: 'dp3', name: 'kaduna_central', fee: 1200 },
];

const produceTotal = computed(() => (props.product?.price || 0) * quantity.value);
const deliveryFee = computed(() => selectedLocation.value?.fee || 0);
const grandTotal = computed(() => produceTotal.value + deliveryFee.value);

const increment = () => quantity.value++;
const decrement = () => { if (quantity.value > 1) quantity.value--; };

/**
 * TRIGGER: This launches the Interswitch UI
 */
const handlePayment = async () => {
  if (isProcessing.value || !props.product || !selectedLocation.value) return;

  isProcessing.value = true;
  try {
    // 1. Create the Order in your DB
    const orderRes = await api.post('/orders/create', {
        items:[ {product_id: props.product.id,
      quantity: quantity.value}],
     delivery_location: selectedLocation.value.name
    });

    const orderId = orderRes.order_id;

    // 2. Get Signed Payment Params from Node.js
    const payData = await api.post(`/payments/initiate/${orderId}`);
    console.log(payData)

    /**
     * 3. Redirect to Squad Authorization URL
     * Squad usually returns a structure like: 
     * { status: 200, data: { checkout_url: "...", access_code: "..." } }
     */
    if (payData.checkout_url) {
      // Redirecting the user to the Squad payment page
      window.location.href = payData.checkout_url;
    } else if (payData.data?.checkout_url) {
      // Fallback if your backend sends the nested Squad 'data' object
      window.location.href = payData.data.checkout_url;
    } else {
      throw new Error("Checkout URL not found in payment response");
    }

  } catch (err) {
    console.error("Squad Flow Error:", err);
    const errorMsg = err.response?.data?.message || "Could not initialize payment.";
    alert(`Payment Error: ${errorMsg}`);
  } finally {
    isProcessing.value = false;
  }
};
</script>

<template>
  <div v-if="isOpen" class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-[#061209]/95 backdrop-blur-xl">
    <div class="bg-[#0d2010] border border-white/10 w-full max-w-md rounded-[3rem] p-8 md:p-10 relative shadow-2xl overflow-y-auto max-h-[90vh]">
      
      <button @click="$emit('close')" class="absolute top-8 right-8 text-white/20 hover:text-white transition-colors">
        <X :size="20" />
      </button>

      <div class="text-center mb-6">
        <div class="w-14 h-14 bg-[#5cb83a]/10 rounded-full flex items-center justify-center mx-auto mb-4 border border-[#5cb83a]/20 text-[#5cb83a]">
          <Lock :size="24" />
        </div>
        <h2 class="text-2xl font-serif text-[#f0ede4]">Secure Escrow</h2>
        <p class="text-white/40 text-[10px] uppercase tracking-widest mt-1">Interswitch Multi-party Settlement</p>
      </div>

      <div class="bg-white/5 rounded-3xl p-5 mb-6 border border-white/5">
        <label class="text-[9px] uppercase tracking-[0.2em] text-white/30 mb-3 block text-center font-bold">Quantity ({{ product?.unit_type || 'Unit' }})</label>
        <div class="flex items-center justify-between px-6">
          <button @click="decrement" class="w-10 h-10 rounded-full border border-white/10 flex items-center justify-center hover:bg-white/5 transition-all text-white"><Minus :size="16" /></button>
          <span class="text-3xl font-serif text-[#f0ede4]">{{ quantity }}</span>
          <button @click="increment" class="w-10 h-10 rounded-full border border-white/10 flex items-center justify-center hover:bg-white/5 transition-all text-white"><Plus :size="16" /></button>
        </div>
      </div>

      <div class="mb-6">
        <label class="text-[9px] uppercase tracking-[0.2em] text-white/30 mb-3 block font-bold ml-1">Drop-off Point</label>
        <div class="space-y-2">
          <button 
            v-for="point in dropOffPoints" :key="point.id"
            @click="selectedLocation = point"
            class="w-full flex items-center justify-between p-4 rounded-2xl border text-left transition-all"
            :class="selectedLocation?.id === point.id ? 'border-[#5cb83a] bg-[#5cb83a]/10' : 'border-white/5 bg-white/5 hover:bg-white/10'"
          >
            <div class="flex items-center gap-3">
              <MapPin :size="14" :class="selectedLocation?.id === point.id ? 'text-[#5cb83a]' : 'text-white/20'" />
              <span class="text-xs font-medium" :class="selectedLocation?.id === point.id ? 'text-white' : 'text-white/60'">{{ point.name }}</span>
            </div>
            <span class="text-[10px] font-bold text-[#5cb83a]">₦{{ point.fee }}</span>
          </button>
        </div>
      </div>

      <div class="space-y-4 mb-8 bg-black/20 p-5 rounded-3xl border border-white/5">
        <div class="space-y-2 text-xs">
          <div class="flex justify-between text-white/40 font-medium">
            <span>Produce Total</span>
            <span>₦{{ produceTotal.toLocaleString() }}</span>
          </div>
          <div class="flex justify-between text-white/40 font-medium">
            <span>Delivery Fee</span>
            <span>₦{{ deliveryFee.toLocaleString() }}</span>
          </div>
        </div>
        <div class="flex justify-between items-center pt-2 border-t border-white/10">
          <span class="font-bold uppercase text-[10px] tracking-widest text-white/60">Grand Total</span>
          <span class="text-3xl font-serif text-[#f0ede4]">₦{{ grandTotal.toLocaleString() }}</span>
        </div>
      </div>

      <button 
        @click="handlePayment" 
        :disabled="isProcessing || !selectedLocation"
        class="w-full bg-[#5cb83a] hover:bg-[#4ea131] text-[#061209] py-5 rounded-2xl font-bold flex items-center justify-center gap-2 transition-all disabled:opacity-30 active:scale-[0.98] shadow-lg shadow-[#5cb83a]/20"
      >
        <template v-if="!isProcessing">
          <ShieldCheck :size="20" /> 
          Authorize Escrow
        </template>
        <template v-else>
          <Loader2 class="animate-spin" :size="20" />
          Processing...
        </template>
      </button>

      <p class="text-[8px] text-center text-white/20 mt-4 leading-relaxed uppercase tracking-tighter">
        🔒 Funds are held by Interswitch and only released upon your confirmation.
      </p>
    </div>
  </div>
</template>