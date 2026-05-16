<script setup>
import { onMounted, ref } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import api from '@/api/api';
import { CheckCircle2, ArrowRight, Loader2, XCircle } from 'lucide-vue-next';

const route = useRoute();
const router = useRouter();
const status = ref('verifying'); // verifying, success, error
const orderDetails = ref(null);

const verifyPayment = async () => {
  const txRef = route.query.transaction_ref || route.query.reference;
  
  if (!txRef) {
    status.value = 'error';
    return;
  }

  try {
    // Your backend endpoint should verify the transaction with Squad
    const response = await api.get(`/payments/verify/${txRef}`);
    
    if (response.data.status === 'success') {
      orderDetails.value = response.data.order;
      status.value = 'success';
    } else {
      status.value = 'error';
    }
  } catch (err) {
    console.error("Verification failed:", err);
    status.value = 'error';
  }
};

onMounted(verifyPayment);
</script>

<template>
  <div class="min-h-screen bg-[#061209] text-[#f0ede4] flex items-center justify-center p-6">
    <div class="max-w-md w-full bg-[#0d2010] border border-white/10 rounded-[3rem] p-10 text-center shadow-2xl">
      
      <div v-if="status === 'verifying'" class="space-y-6">
        <Loader2 class="animate-spin text-[#5cb83a] mx-auto" :size="64" />
        <h2 class="text-2xl font-serif">Verifying Payment</h2>
        <p class="text-white/40 text-sm">Please wait while we confirm your transaction with Squad.</p>
      </div>

      <div v-if="status === 'success'" class="space-y-8">
        <div class="relative inline-block">
          <div class="absolute inset-0 bg-[#5cb83a] blur-3xl opacity-20 animate-pulse"></div>
          <CheckCircle2 class="text-[#5cb83a] relative z-10" :size="80" />
        </div>
        
        <div>
          <h2 class="text-3xl font-serif mb-2">Payment Secured</h2>
          <p class="text-white/40 text-sm">Your funds are now held in escrow. The farmer has been notified to begin dispatch.</p>
        </div>

        <div class="bg-black/20 border border-white/5 rounded-2xl p-4 text-left">
          <div class="flex justify-between text-xs mb-2">
            <span class="opacity-40 uppercase">Transaction Ref</span>
            <span class="font-mono text-[#5cb83a]">{{ route.query.transaction_ref?.slice(0, 15) }}...</span>
          </div>
          <div class="flex justify-between text-xs">
            <span class="opacity-40 uppercase">Amount Paid</span>
            <span class="font-bold">₦{{ orderDetails?.total_amount?.toLocaleString() || '---' }}</span>
          </div>
        </div>

        <button 
          @click="router.push('/dashboard')"
          class="w-full bg-[#5cb83a] hover:bg-[#4da330] text-[#061209] font-bold py-4 rounded-2xl flex items-center justify-center gap-2 transition-all"
        >
          Go to Dashboard <ArrowRight :size="18" />
        </button>
      </div>

      <div v-if="status === 'error'" class="space-y-6">
        <XCircle class="text-red-500 mx-auto" :size="80" />
        <h2 class="text-2xl font-serif">Payment Issue</h2>
        <p class="text-white/40 text-sm">We couldn't verify your payment. If you were debited, please contact support with your reference ID.</p>
        
        <button 
          @click="router.push('/marketplace')"
          class="w-full border border-white/10 hover:bg-white/5 py-4 rounded-2xl transition-all"
        >
          Return to Marketplace
        </button>
      </div>

    </div>
  </div>
</template>