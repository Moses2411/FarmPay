<script setup>
import { useRoute, useRouter } from 'vue-router';
import api from '@/api/api';
import { useAuthStore } from '../../stores/auth';
import { CheckCircle2, ArrowRight, Loader2, XCircle } from 'lucide-vue-next';

const route = useRoute();
const router = useRouter();
const auth = useAuthStore();
const status = ref('verifying'); // verifying, success, error
const orderDetails = ref(null);
const verifyPayment = async () => {
  const txRef = route.query.transaction_ref || route.query.reference;
  
  if (!txRef) {
    status.value = 'error';
    return;
  }

  try {
    // Send the POST request as required by Swagger
    const response = await api.post(`/payments/verify`, {
      transaction_ref: txRef
    });
    
    const result = response.data || response;

    /**
     * REWIRED LOGIC:
     * Your response contains "escrow_status": "held" 
     * and sometimes a message like "Payment already confirmed".
     */
    if (result.escrow_status === 'held' || result.message === 'Payment already confirmed') {
      // Store the result (contains order_id and escrow_status)
      orderDetails.value = result;
      status.value = 'success';
    } else {
      status.value = 'error';
    }
  } catch (err) {
    // Even if it's a 400 error, if the message says "already confirmed", it's a success
    const errorData = err.response?.data;
    if (errorData?.message === 'Payment already confirmed' || errorData?.escrow_status === 'held') {
      orderDetails.value = errorData;
      status.value = 'success';
    } else {
      console.error("Verification failed:", err);
      status.value = 'error';
    }
  }
};

onMounted(verifyPayment);
</script>

<template>
  <div class="min-h-screen bg-[#061209] text-[#f0ede4] flex items-center justify-center p-6">
    <div class="max-w-md w-full bg-[#0d2010] border border-white/10 rounded-[3rem] p-10 text-center shadow-2xl">
      
      <div v-if="status === 'verifying'" class="space-y-6">
        <Loader2 class="animate-spin text-[#5cb83a] mx-auto" :size="64" />
        <h2 class="text-2xl font-serif">Confirming Transfer</h2>
        <p class="text-white/40 text-sm">Validating your transaction with the Squad network...</p>
      </div>

      <div v-if="status === 'success'" class="space-y-8">
        <div class="relative inline-block">
          <div class="absolute inset-0 bg-[#5cb83a] blur-3xl opacity-20 animate-pulse"></div>
          <CheckCircle2 class="text-[#5cb83a] relative z-10" :size="80" />
        </div>
        
        <div>
          <h2 class="text-3xl font-serif mb-2">Escrow Activated</h2>
          <p class="text-white/40 text-sm">Order #{{ orderDetails?.order_id?.slice(0, 8).toUpperCase() }} is now secured. The farmer is preparing your shipment.</p>
        </div>

        <div class="bg-black/20 border border-white/5 rounded-2xl p-5 text-left space-y-3">
          <div class="flex justify-between text-[10px]">
            <span class="opacity-40 uppercase tracking-widest">Order Reference</span>
            <span class="font-mono text-[#5cb83a]">{{ orderDetails?.order_id?.slice(0, 13) }}...</span>
          </div>
          <div class="flex justify-between text-[10px]">
            <span class="opacity-40 uppercase tracking-widest">Escrow Status</span>
            <span class="text-[#5cb83a] font-bold uppercase tracking-tighter">● {{ orderDetails?.escrow_status }}</span>
          </div>
        </div>

        <button 
          @click="router.push(`/${auth.user.role}`)"
          class="w-full bg-[#5cb83a] hover:bg-[#4da330] text-[#061209] font-bold py-4 rounded-2xl flex items-center justify-center gap-2 transition-all active:scale-95"
        >
          View in Dashboard <ArrowRight :size="18" />
        </button>
      </div>

      <div v-if="status === 'error'" class="space-y-6">
        <XCircle class="text-red-500 mx-auto" :size="80" />
        <h2 class="text-2xl font-serif">Verification Failed</h2>
        <p class="text-white/40 text-sm">We couldn't find a record of this payment. If your account was debited, please wait a moment and refresh.</p>
        
        <div class="flex flex-col gap-3">
           <button @click="verifyPayment" class="w-full bg-white/10 hover:bg-white/20 py-4 rounded-2xl transition-all font-bold">
            Retry Verification
          </button>
          <button @click="router.push('/marketplace')" class="w-full text-white/40 hover:text-white text-xs uppercase tracking-widest">
            Back to Marketplace
          </button>
        </div>
      </div>

    </div>
  </div>
</template>