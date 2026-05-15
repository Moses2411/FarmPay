<script setup>
import { ref, computed } from 'vue';
import api from '@/api/api';
import { Minus, Plus, ShieldCheck, Lock, X, Loader2 } from 'lucide-vue-next';

const props = defineProps(['product', 'isOpen']);
const emit = defineEmits(['close', 'payment-success']);

const isProcessing = ref(false);
const quantity = ref(1);

// Address Refs
const deliveryAddress = ref('');
const buyerAddress = ref('');

// Logic Constants
const produceTotal = computed(() => (props.product?.price || 0) * quantity.value);
const deliveryFee = computed(() => 5000); // Fixed fallback as requested
const grandTotal = computed(() => produceTotal.value + deliveryFee.value);

const increment = () => quantity.value++;
const decrement = () => { if (quantity.value > 1) quantity.value--; };

/**
 * TRIGGER: Order creation and Squad Payment Redirection
 */
const handlePayment = async () => {
  // Validate that we have the necessary strings before proceeding
  if (isProcessing.value || !props.product || !deliveryAddress.value || !buyerAddress.value) {
    return;
  }

  isProcessing.value = true;
  try {
    // 1. Create the Order in the DB matching Swagger Requirements
    const orderRes = await api.post('/orders/create', {
      items: [{ 
        product_id: props.product.id, 
        quantity: quantity.value 
      }],
      delivery_address: deliveryAddress.value,
      buyer_address: buyerAddress.value
    });

    // Extract Order ID (handling potential Axios wrapper)
    const orderData = orderRes.data || orderRes;
    const orderId = orderData.order_id || orderData.id;

    // 2. Get Signed Payment Params for Squad
    const payRes = await api.post(`/payments/initiate/${orderId}`);
    const payData = payRes.data || payRes;

    // 3. Redirect to Squad Authorization URL
    const checkoutUrl = payData.checkout_url || payData.data?.checkout_url;
    
    if (checkoutUrl) {
      window.location.href = checkoutUrl;
    } else {
      throw new Error("Checkout URL not found in payment response");
    }

  } catch (err) {
    console.error("Payment Flow Error:", err);
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
      
      <button @click="$emit('close')" class="absolute top-8 right-8 text-white/20 hover:text-white transition-colors cursor-pointer">
        <X :size="20" />
      </button>

      <div class="text-center mb-6">
        <div class="w-14 h-14 bg-[#5cb83a]/10 rounded-full flex items-center justify-center mx-auto mb-4 border border-[#5cb83a]/20 text-[#5cb83a]">
          <Lock :size="24" />
        </div>
        <h2 class="text-2xl font-serif text-[#f0ede4]">Secure Escrow</h2>
        <p class="text-white/40 text-[10px] uppercase tracking-widest mt-1">Squad Multi-party Settlement</p>
      </div>

      <div class="bg-white/5 rounded-3xl p-5 mb-6 border border-white/5">
        <label class="text-[9px] uppercase tracking-[0.2em] text-white/30 mb-3 block text-center font-bold">Quantity ({{ product?.unit_type || 'Unit' }})</label>
        <div class="flex items-center justify-between px-6">
          <button @click="decrement" class="w-10 h-10 rounded-full border border-white/10 flex items-center justify-center hover:bg-white/5 transition-all text-white cursor-pointer"><Minus :size="16" /></button>
          <span class="text-3xl font-serif text-[#f0ede4]">{{ quantity }}</span>
          <button @click="increment" class="w-10 h-10 rounded-full border border-white/10 flex items-center justify-center hover:bg-white/5 transition-all text-white cursor-pointer"><Plus :size="16" /></button>
        </div>
      </div>

      <div class="mb-6">
        <label class="text-[10px] uppercase tracking-[0.2em] text-white/30 mb-3 block font-bold ml-1">
          Delivery Address
        </label>
        <textarea 
          v-model="deliveryAddress"
          placeholder="Detailed street address, nearest landmark, and city..."
          rows="3"
          class="w-full bg-white/5 border border-white/10 rounded-[1.5rem] p-4 text-sm text-[#f0ede4] placeholder:text-white/20 focus:border-[#5cb83a] focus:bg-white/[0.07] outline-none transition-all resize-none leading-relaxed"
        ></textarea>
        <p class="text-[8px] text-white/20 mt-2 ml-2 uppercase tracking-widest">
          Rider will use this text to find your location.
        </p>
      </div>

      <div class="mb-6">
        <label class="text-[9px] uppercase tracking-widest text-white/30 mb-2 block font-bold ml-1">
          Buyer's House No. / Billing Address
        </label>
        <textarea 
          v-model="buyerAddress"
          placeholder="House No., Apartment, or Billing address..."
          rows="2"
          class="w-full bg-white/5 border border-white/10 rounded-[1.5rem] p-4 text-sm text-white focus:border-[#5cb83a] outline-none transition-all resize-none placeholder:text-white/20"
        ></textarea>
      </div>

      <div class="space-y-4 mb-8 bg-black/20 p-6 rounded-3xl border border-white/5">
        <div class="space-y-2 text-xs">
          <div class="flex justify-between text-white/40 font-medium">
            <span>Produce Total</span>
            <span>₦{{ produceTotal.toLocaleString() }}</span>
          </div>
          <div class="flex justify-between text-white/40 font-medium">
            <span>Delivery Fee (Flat)</span>
            <span>₦{{ deliveryFee.toLocaleString() }}</span>
          </div>
        </div>
        <div class="flex justify-between items-center pt-3 border-t border-white/10">
          <span class="font-bold uppercase text-[10px] tracking-widest text-white/60">Grand Total</span>
          <span class="text-3xl font-serif text-[#f0ede4]">₦{{ grandTotal.toLocaleString() }}</span>
        </div>
      </div>

      <button 
        @click="handlePayment" 
        :disabled="isProcessing || !deliveryAddress || !buyerAddress"
        class="w-full bg-[#5cb83a] hover:bg-[#4ea131] text-[#061209] py-5 rounded-2xl font-bold flex items-center justify-center gap-2 transition-all disabled:opacity-20 active:scale-[0.98] shadow-lg shadow-[#5cb83a]/20 cursor-pointer"
      >
        <template v-if="!isProcessing">
          <ShieldCheck :size="20" /> 
          Authorize Escrow
        </template>
        <template v-else>
          <Loader2 class="animate-spin" :size="20" />
          Connecting to Squad...
        </template>
      </button>

      <p class="text-[8px] text-center text-white/20 mt-4 leading-relaxed uppercase tracking-tighter">
        🔒 Funds are secured via multi-party escrow and only released upon confirmation.
      </p>
    </div>
  </div>
</template>