<script setup>
import { ref, computed } from 'vue';
import api from '@/api/api';
import { Minus, Plus, ShieldCheck, Lock, X, Loader2 } from 'lucide-vue-next';
import AddressPicker from './marketplace/AddressPicker.vue';
import DeliveryFeeDisplay from './marketplace/DeliveryFeeDisplay.vue';

const props = defineProps(['product', 'isOpen']);
const emit = defineEmits(['close', 'payment-success']);

const isProcessing = ref(false);
const quantity = ref(1);
const errorMessage = ref('');

// Address Refs
const selectedAddress = ref(null);
const buyerAddress = ref('');

// Get product location from farmer profile
const productLocation = computed(() => {
  if (props.product?.farmer?.farmer_profile?.location) {
    return props.product.farmer.farmer_profile.location;
  }
  if (props.product?.location) {
    return props.product.location;
  }
  return 'Kaduna, Nigeria';
});

// Calculate totals
const produceTotal = computed(() => (props.product?.price || 0) * quantity.value);
const grandTotal = computed(() => {
  const deliveryFee = selectedAddress.value?.deliveryFee || 2000;
  return produceTotal.value + deliveryFee;
});

const deliveryFee = computed(() => selectedAddress.value?.deliveryFee || 2000);

const increment = () => quantity.value++;
const decrement = () => { if (quantity.value > 1) quantity.value--; };

const handleAddressSelect = (location) => {
  selectedAddress.value = location;
};

/**
 * TRIGGER: Order creation and Squad Payment Redirection
 */
const handlePayment = async () => {
  if (isProcessing.value || !props.product || !selectedAddress.value || !buyerAddress.value) {
    errorMessage.value = 'Please fill in all required fields';
    return;
  }

  isProcessing.value = true;
  errorMessage.value = '';

  try {
    const orderRes = await api.post('/orders/create', {
      items: [{
        product_id: props.product.id,
        quantity: quantity.value
      }],
      delivery_address: selectedAddress.value.place_name || `${selectedAddress.value.address}, ${selectedAddress.value.city}`,
    });

    const orderId = orderRes.order_id || orderRes.id;

    const payRes = await api.post(`/payments/initiate/${orderId}`);
    const checkoutUrl = payRes.checkout_url || payRes.data?.checkout_url;

    if (checkoutUrl) {
      window.location.href = checkoutUrl;
    } else {
      throw new Error("Checkout URL not found in payment response");
    }

  } catch (err) {
    console.error("Payment Flow Error:", err);
    errorMessage.value = err.detail || "Could not initialize payment.";
  } finally {
    isProcessing.value = false;
  }
};
</script>

<template>
  <div v-if="isOpen" class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-[#061209]/95 backdrop-blur-xl">
    <div class="bg-[#0d2010] border border-white/10 w-full max-w-lg rounded-[3rem] p-8 relative shadow-2xl overflow-y-auto max-h-[90vh]">
      
      <button @click="$emit('close')" class="absolute top-6 right-6 text-white/20 hover:text-white transition-colors cursor-pointer">
        <X :size="20" />
      </button>

      <!-- Product Info Header -->
      <div class="flex items-center gap-4 mb-6 pb-6 border-b border-white/10">
        <div class="w-16 h-16 rounded-2xl bg-black/30 overflow-hidden flex-shrink-0">
          <img 
            :src="product?.images?.[0]?.image_url || 'https://via.placeholder.com/100?text=Produce'" 
            class="w-full h-full object-cover"
          />
        </div>
        <div class="flex-1 min-w-0">
          <h3 class="font-serif text-lg text-white truncate">{{ product?.name }}</h3>
          <p class="text-[#5cb83a] font-bold">₦{{ (product?.price || 0).toLocaleString() }} <span class="text-white/30 text-xs">per {{ product?.unit_type || 'unit' }}</span></p>
        </div>
      </div>

      <!-- Quantity Selector -->
      <div class="bg-white/5 rounded-2xl p-4 mb-6 border border-white/5">
        <label class="text-[9px] uppercase tracking-[0.2em] text-white/30 mb-3 block text-center font-bold">Quantity</label>
        <div class="flex items-center justify-center gap-6">
          <button @click="decrement" class="w-10 h-10 rounded-full border border-white/10 flex items-center justify-center hover:bg-white/5 transition-all text-white cursor-pointer disabled:opacity-30" :disabled="quantity <= 1">
            <Minus :size="16" />
          </button>
          <span class="text-3xl font-serif text-[#f0ede4] w-12 text-center">{{ quantity }}</span>
          <button @click="increment" class="w-10 h-10 rounded-full border border-white/10 flex items-center justify-center hover:bg-white/5 transition-all text-white cursor-pointer">
            <Plus :size="16" />
          </button>
        </div>
      </div>

      <!-- Address Selection -->
      <div class="mb-6">
        <AddressPicker 
          :product-location="productLocation"
          @select="handleAddressSelect"
          placeholder="Search for your delivery location..."
          label="Delivery Location"
        />
      </div>

      <!-- Delivery Fee Display -->
      <div v-if="selectedAddress" class="mb-6">
        <DeliveryFeeDisplay 
          :product-location="productLocation"
          :delivery-address="selectedAddress"
          :base-delivery-fee="2000"
        />
      </div>

      <!-- Buyer Address (Additional Info) -->
      <div class="mb-6">
        <label class="text-[10px] uppercase tracking-[0.2em] text-white/30 mb-2 block font-bold ml-1">
          Additional Delivery Notes
        </label>
        <textarea 
          v-model="buyerAddress"
          placeholder="House number, landmark, gate code, instructions for rider..."
          rows="2"
          class="w-full bg-white/5 border border-white/10 rounded-xl p-4 text-sm text-white focus:border-[#5cb83a] outline-none transition-all resize-none placeholder:text-white/20"
        ></textarea>
      </div>

      <!-- Error Message -->
      <div v-if="errorMessage" class="mb-4 p-3 bg-red-500/10 border border-red-500/20 rounded-xl text-red-400 text-xs">
        {{ errorMessage }}
      </div>

      <!-- Order Summary -->
      <div class="space-y-3 mb-6 bg-black/20 p-5 rounded-2xl border border-white/5">
        <div class="flex justify-between text-xs text-white/50">
          <span>Produce ({{ quantity }} {{ product?.unit_type || 'unit' }})</span>
          <span>₦{{ produceTotal.toLocaleString() }}</span>
        </div>
        <div class="flex justify-between text-xs text-white/50">
          <span>Delivery Fee</span>
          <span>₦{{ deliveryFee.toLocaleString() }}</span>
        </div>
        <div class="flex justify-between items-center pt-3 border-t border-white/10">
          <span class="font-bold uppercase text-[10px] tracking-widest text-white/60">Total</span>
          <span class="text-2xl font-serif text-[#5cb83a]">₦{{ grandTotal.toLocaleString() }}</span>
        </div>
      </div>

      <!-- Pay Button -->
      <button 
        @click="handlePayment" 
        :disabled="isProcessing || !selectedAddress || !buyerAddress"
        class="w-full bg-[#5cb83a] hover:bg-[#4ea131] text-[#061209] py-5 rounded-2xl font-bold flex items-center justify-center gap-2 transition-all disabled:opacity-20 active:scale-[0.98] shadow-lg shadow-[#5cb83a]/20 cursor-pointer"
      >
        <template v-if="!isProcessing">
          <ShieldCheck :size="20" /> 
          Authorize Escrow Payment
        </template>
        <template v-else>
          <Loader2 class="animate-spin" :size="20" />
          Processing...
        </template>
      </button>

      <p class="text-[8px] text-center text-white/20 mt-4 leading-relaxed">
        🔒 Funds are secured via multi-party escrow and only released upon delivery confirmation.
      </p>
    </div>
  </div>
</template>