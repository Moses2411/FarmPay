<script setup>
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import { useForm, useField } from 'vee-validate';
import * as yup from 'yup';
import { useAuthStore } from '../../stores/auth';
import { completeProfile as completeProfileApi, getUserProfile } from '../../api/api';
import { 
  Wallet, MapPin, ShieldCheck, Landmark, Fingerprint, 
  ArrowRight, Info, Loader2, AlertCircle, CheckCircle2, Store
} from 'lucide-vue-next';

const router = useRouter();
const auth = useAuthStore();
const serverError = ref('');

const kadunaData = {
  'North': ['Sabon Gari', 'Zaria', 'Ikara', 'Makarfi', 'Soba', 'Kudan', 'Kubau'],
  'Central': ['Birnin Gwari', 'Chikun', 'Giwa', 'Igabi', 'Kaduna North', 'Kaduna South', 'Kajuru'],
  'South': ['Jaba', 'Jema\'a', 'Kachia', 'Kagarko', 'Kaura', 'Kauru', 'Lere', 'Sanga', 'Zangon Kataf']
};

const zones = Object.keys(kadunaData);

// 2. Updated Validation Schema
const schema = yup.object({
  businessName: yup.string().required('Business/Farm name is required').min(3, 'Too short'),
  zone: yup.string().required('Please select your agricultural zone'),
  lga: yup.string().required('Please select your Local Government Area'),
  idNumber: yup.string()
    .required('Verification ID is required')
    .matches(/^[0-9]{10,11}$/, 'ID must be 10 (BVN) or 11 (NIN) digits'),
  address: yup.string().required('Farm/Contact address is required').min(10, 'Please provide a full address'),
  bankName: yup.string().required('Please select a bank'),
  accountNumber: yup.string().required('Account number is required').length(10, 'Must be exactly 10 digits'),
});

const { handleSubmit, errors, isSubmitting } = useForm({
  validationSchema: schema,
  initialValues: {
    zone: '',
    lga: '',
    bankName: ''
  }
});

const { value: businessName } = useField('businessName');
const { value: zone } = useField('zone');
const { value: lga } = useField('lga');
const { value: idNumber } = useField('idNumber');
const { value: address } = useField('address');
const { value: bankName } = useField('bankName');
const { value: accountNumber } = useField('accountNumber');

const onComplete = handleSubmit(async (values) => {
  serverError.value = '';
  try {
    // const farmerProfile = await completeProfileApi({
    //   business_name: values.businessName,
    //   zone: values.zone,
    //   lga: values.lga,
    //   address: values.address,
    //   nin_bvn: values.idNumber,
    //   bank_name: values.bankName,
    //   account_number: values.accountNumber
    // });
    const farmerProfile = await completeProfileApi({
      business_name: values.businessName,
     location: `kaduna_${values.zone.toLowerCase()}`,
     nin: values.idNumber,
     bank_name: values.bankName,
     account_number: values.accountNumber
    });

    console.log(farmerProfile)

     auth.user.profile = farmerProfile;
     auth.setVerified(true);
     const updatedUser = auth.user;
    auth.setAuth(updatedUser, auth.token);
    router.push({ name: 'FarmerDashboard' });

  } catch (err) {
    serverError.value = err.response?.data?.detail || "Verification failed. Check your ID/Account details.";
  }
});
</script>

<template>
  <div class="min-h-screen bg-[#061209] flex flex-col lg:flex-row font-sans text-[#f0ede4]">
    
    <div class="hidden lg:flex lg:w-5/12 bg-[#0d2010] p-12 flex-col justify-between border-r border-white/5">
      <div>
        <div class="flex items-center gap-3 mb-16">
          <div class="w-8 h-8 bg-[#2d7a18] rounded-full flex items-center justify-center">
            <Wallet class="text-white" :size="16" />
          </div>
          <span class="font-serif text-xl font-semibold tracking-tight">FarmPay<span class="text-[#5cb83a]">.</span>ng</span>
        </div>

        <h2 class="font-serif text-5xl leading-tight mb-8">
          Verify your <br/>
          <span class="text-[#5cb83a] italic">Farmer Identity.</span>
        </h2>

        <div class="space-y-6">
          <div class="flex gap-4 items-start">
            <div class="mt-1 text-[#5cb83a]"><Store :size="20" /></div>
            <div>
              <p class="font-bold text-sm">Business Profile</p>
              <p class="text-xs text-white/40">Your farm name appears on Interswitch payment receipts to buyers.</p>
            </div>
          </div>
          <div class="flex gap-4 items-start">
            <div class="mt-1 text-[#5cb83a]"><Landmark :size="20" /></div>
            <div>
              <p class="font-bold text-sm">Zonal Logistics</p>
              <p class="text-xs text-white/40">We use your Zone to calculate flat-rate transport fares for riders.</p>
            </div>
          </div>
          <div class="flex gap-4 items-start">
            <div class="mt-1 text-[#5cb83a]"><Fingerprint :size="20" /></div>
            <div>
              <p class="font-bold text-sm">Secure Payouts</p>
              <p class="text-xs text-white/40">NIN/BVN verification ensures funds are released to the right person.</p>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div class="flex-1 flex items-center justify-center p-6 md:p-12 overflow-y-auto">
      <div class="w-full max-w-md space-y-8 py-10">
        
        <div class="text-center lg:text-left">
          <div class="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-[#e6a817]/10 border border-[#e6a817]/20 text-[#e6a817] text-[10px] font-bold uppercase tracking-widest mb-4">
            <Info :size="12" /> Final Step: Verification
          </div>
          <h1 class="text-3xl font-serif mb-2">Complete Profile</h1>
          <p class="text-white/40 text-sm">Onboard your farm to start receiving secure payments.</p>
        </div>

        <div v-if="serverError" class="p-4 bg-red-500/10 border border-red-500/20 rounded-xl flex items-center gap-3 text-red-400 text-xs">
          <AlertCircle :size="16" />
          {{ serverError }}
        </div>

        <form @submit.prevent="onComplete" class="space-y-5 text-left">
          
          <div class="space-y-1">
            <label class="text-[10px] uppercase font-bold text-white/30 ml-1">Business / Farm Name</label>
            <div class="relative">
              <Store class="absolute left-4 top-1/2 -translate-y-1/2 text-white/20" :size="18" />
              <input v-model="businessName" type="text" placeholder="e.g. Zaria Green Hub"
                :class="errors.businessName ? 'border-red-500/50' : 'border-white/10'"
                class="w-full bg-white/5 border rounded-xl py-4 pl-12 pr-4 focus:outline-none focus:border-[#5cb83a] transition-colors">
            </div>
            <span class="text-red-400 text-[10px] ml-1">{{ errors.businessName }}</span>
          </div>

          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div class="space-y-1">
              <label class="text-[10px] uppercase font-bold text-white/30 ml-1">Kaduna Zone</label>
              <select v-model="zone" @change="lga = ''"
                :class="errors.zone ? 'border-red-500/50' : 'border-white/10'"
                class="w-full bg-white/5 border rounded-xl p-4 hover:cursor-pointer focus:outline-none focus:border-[#5cb83a] transition-colors appearance-none">
                <option value="" disabled>Select Zone</option>
                <option v-for="z in zones" :key="z" :value="z" class="bg-[#0d2010]">{{ z }}</option>
              </select>
            </div>

            <div class="space-y-1">
              <label class="text-[10px] uppercase font-bold text-white/30 ml-1">LGA</label>
              <select v-model="lga" :disabled="!zone"
                :class="errors.lga ? 'border-red-500/50' : 'border-white/10'"
                class="w-full bg-white/5 border rounded-xl p-4 focus:outline-none focus:border-[#5cb83a] transition-colors appearance-none disabled:opacity-30">
                <option value="" disabled>Select LGA</option>
                <option v-for="item in kadunaData[zone]" :key="item" :value="item" class="bg-[#0d2010]">{{ item }}</option>
              </select>
            </div>
          </div>

          <div class="space-y-1">
            <label class="text-[10px] uppercase font-bold text-white/30 ml-1">Farm / Pickup Address</label>
            <textarea v-model="address" rows="2" placeholder="Full address for rider pickups..."
              :class="errors.address ? 'border-red-500/50' : 'border-white/10'"
              class="w-full bg-white/5 border rounded-xl py-4 px-4 focus:outline-none focus:border-[#5cb83a] transition-colors resize-none"></textarea>
          </div>

          <div class="space-y-1">
            <label class="text-[10px] uppercase font-bold text-white/30 ml-1">NIN or BVN Number</label>
            <div class="relative">
              <Fingerprint class="absolute left-4 top-1/2 -translate-y-1/2 text-white/20" :size="18" />
              <input v-model="idNumber" type="text" maxlength="11" placeholder="11-digit NIN or 10-digit BVN"
                :class="errors.idNumber ? 'border-red-500/50' : 'border-white/10'"
                class="w-full bg-white/5 border rounded-xl py-4 pl-12 pr-4 focus:outline-none focus:border-[#5cb83a] transition-colors">
            </div>
          </div>

          <div class="pt-4 border-t border-white/5 space-y-4">
            <div class="flex items-center gap-2">
              <Landmark class="text-[#5cb83a]" :size="16" />
              <label class="text-[10px] uppercase font-bold text-white/30">Settlement (Interswitch Payout)</label>
            </div>
            
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
              <select v-model="bankName" :class="errors.bankName ? 'border-red-500/50' : 'border-white/10'"
                class="w-full bg-white/5 border rounded-xl p-4 outline-none focus:border-[#5cb83a] appearance-none">
                <option value="" disabled>Select Bank</option>
                <option value="Access Bank">Access Bank</option>
                <option value="First Bank">First Bank</option>
                <option value="GTBank">GTBank</option>
                <option value="Kuda Bank">Kuda Bank</option>
                <option value="Zenith Bank">Zenith Bank</option>
              </select>

              <div class="relative">
                <input v-model="accountNumber" type="text" maxlength="10" placeholder="10-digit NUBAN"
                  :class="errors.accountNumber ? 'border-red-500/50' : 'border-white/10'"
                  class="w-full bg-white/5 border rounded-xl p-4 outline-none focus:border-[#5cb83a]">
                <CheckCircle2 v-if="accountNumber?.length === 10" class="absolute right-4 top-1/2 -translate-y-1/2 text-[#5cb83a]" :size="16" />
              </div>
            </div>
            <p class="text-[10px] text-white/20 italic">Ensures funds reach your bank account after delivery release.</p>
          </div>

          <div class="p-4 bg-white/5 border border-white/10 rounded-xl flex gap-3 italic">
            <ShieldCheck class="text-[#5cb83a] shrink-0" :size="16" />
            <p class="text-[10px] text-white/40 leading-relaxed">
              Your data is encrypted. We only use this ID to verify identity via Nigerian financial registries.
            </p>
          </div>

          <button type="submit" :disabled="isSubmitting"
            class="w-full bg-[#2d7a18] hover:bg-[#3a9e20] text-white py-4 rounded-xl font-bold flex items-center justify-center gap-2 transition-all disabled:opacity-50 shadow-lg shadow-[#2d7a18]/10">
            <Loader2 v-if="isSubmitting" class="animate-spin" :size="20" />
            <span v-if="!isSubmitting">Complete Setup & Get Started</span>
            <span v-else>Verifying Identity...</span>
            <ArrowRight v-if="!isSubmitting" :size="18" />
          </button>
        </form>
      </div>
    </div>
  </div>
</template>