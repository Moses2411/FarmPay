<script setup>
import { ref } from 'vue';
import { useForm, useField } from 'vee-validate';
import * as yup from 'yup';
import { 
  Wallet, User, Sprout, ShieldCheck, ArrowRight, 
  CheckCircle2, Mail, Lock, Phone 
} from 'lucide-vue-next';
import { register as registerApi, login as loginApi } from '../../api/api';
import { useRouter } from 'vue-router';
import { useAuthStore } from '../../stores/auth';

const role = ref('buyer'); 
const auth = useAuthStore();
const router = useRouter();

// 1. Define the Validation Schema using Yup
const schema = yup.object({
  fullName: yup.string().required('Full name is required').min(3, 'Name too short'),
  email: yup.string().required('Email is required').email('Enter a valid email'),
  phone: yup.string()
    .required('Phone number is required')
    .matches(/^[0-9]{11}$/, 'Phone must be exactly 11 digits (e.g. 08012345678)'),
  password: yup.string().required('Password is required').min(8, 'Password must be at least 8 characters'),
});

// 2. Initialize Vee-Validate Form
const { handleSubmit, errors, isSubmitting } = useForm({
  validationSchema: schema,
  initialValues: {
    fullName: '',
    email: '',
    phone: '',
    password: ''
  }
});

// 3. Define individual fields for manual binding
const { value: fullName } = useField('fullName');
const { value: email } = useField('email');
const { value: phone } = useField('phone');
const { value: password } = useField('password');

// 4. Form Submission Handler
const onSignup = handleSubmit(async (values) => {
  console.log('Form Submitted!', { ...values, role: role.value });
  // API Call: POST /auth/register
 try {
    const payload = {
      full_name: values.fullName,
      email: values.email,
      role: role.value, // 'farmer' or 'buyer'
      password: values.password,
      phone_number: values.phone
    };

    // 1. Register the user
    const newUser = await registerApi(payload);
    console.log('User registered:', newUser);

    // 2. DECISION LOGIC:
    if (role.value === 'farmer') {
      // For Farmers: Auto-login and redirect to complete-profile
      const loginRes = await loginApi({
        email: values.email,
        password: values.password
      });
      auth.setAuth(loginRes, loginRes.access_token);
      return router.push({ name: 'CompleteProfile' });
    }

    // 3. For Buyers: Send to Login
    router.push({
      name: 'Login',
      query: { registered: 'true', message: 'Account created! Please sign in.' }
    });

  } catch (err) {
    // Handle errors (e.g., Email already taken)
    console.error("Registration failed:", err);
  }


});
</script>

<template>
  <div class="min-h-screen bg-[#061209] flex flex-col lg:flex-row font-sans text-[#f0ede4]">
    
    <div class="hidden lg:flex lg:w-5/12 bg-[#0d2010] p-12 flex-col justify-between border-r border-white/5">
      <div>
        <router-link to="/" class="flex items-center gap-3 mb-16">
          <div class="w-8 h-8 bg-[#2d7a18] rounded-full flex items-center justify-center">
            <Wallet class="text-white" :size="16" />
          </div>
          <span class=" text-xl font-semibold tracking-tight">FarmPay<span class="text-[#5cb83a]">.</span>ng</span>
        </router-link>

        <h2 class="font-serif text-5xl leading-tight mb-8">
          Join the most trusted <br/>
          <span class="text-[#5cb83a] italic">Agri-network</span> in Kaduna.
        </h2>

        <div class="space-y-6 text-left">
          <div class="flex gap-4 items-start">
            <div class="mt-1 text-[#5cb83a]"><ShieldCheck :size="20" /></div>
            <div>
              <p class="font-bold">Escrow Protection</p>
              <p class="text-sm text-white/40">Payments are only released when delivery is confirmed.</p>
            </div>
          </div>
          <div class="flex gap-4 items-start">
            <div class="mt-1 text-[#5cb83a]"><CheckCircle2 :size="20" /></div>
            <div>
              <p class="font-bold">Verified Produce</p>
              <p class="text-sm text-white/40">Every harvest listed is AI-scanned for quality assurance.</p>
            </div>
          </div>
        </div>
      </div>
      <div class="text-[10px] uppercase tracking-widest text-white/20 text-left">
        © 2026 FarmPay.ng · Secure Portal
      </div>
    </div>

    <div class="flex-1 flex items-center justify-center p-6 md:p-12">
      <div class="w-full max-w-md space-y-8">
        
        <div class="text-center lg:text-left">
          <h1 class="text-3xl font-serif mb-2">Create Account</h1>
          <p class="text-white/40 text-sm">Join FarmPay to start trading verified produce.</p>
        </div>

        <div class="grid grid-cols-2 gap-4">
          <button type="button" @click="role = 'buyer'"
            :class="role === 'buyer' ? 'border-[#5cb83a] bg-[#5cb83a]/10' : 'border-white/10 bg-white/5'"
            class="flex flex-col items-center p-6 rounded-2xl border transition-all group hover:border-[#5cb83a]/50">
            <div class="w-12 h-12 rounded-full mb-3 flex items-center justify-center transition-colors"
                 :class="role === 'buyer' ? 'bg-[#5cb83a] text-white' : 'bg-white/5 text-white/40'">
              <User :size="24" />
            </div>
            <span class="text-xs font-bold uppercase tracking-widest">Buyer</span>
          </button>

          <button type="button" @click="role = 'farmer'"
            :class="role === 'farmer' ? 'border-[#5cb83a] bg-[#5cb83a]/10' : 'border-white/10 bg-white/5'"
            class="flex flex-col items-center p-6 rounded-2xl border transition-all group hover:border-[#5cb83a]/50">
            <div class="w-12 h-12 rounded-full mb-3 flex items-center justify-center transition-colors"
                 :class="role === 'farmer' ? 'bg-[#5cb83a] text-white' : 'bg-white/5 text-white/40'">
              <Sprout :size="24" />
            </div>
            <span class="text-xs font-bold uppercase tracking-widest">Farmer</span>
          </button>
        </div>

        <form @submit="onSignup" class="space-y-4 text-left">
          <div class="space-y-1">
            <label class="text-[10px] uppercase font-bold text-white/30 ml-1">Full Name</label>
            <div class="relative">
              <User class="absolute left-4 top-1/2 -translate-y-1/2 text-white/20" :size="18" />
              <input v-model="fullName" type="text" placeholder="John Danladi" 
                :class="errors.fullName ? 'border-red-500/50' : 'border-white/10'"
                class="w-full bg-white/5 border rounded-xl py-4 pl-12 pr-4 focus:outline-none focus:border-[#5cb83a] transition-colors">
            </div>
            <span class="text-red-400 text-[10px] ml-1">{{ errors.fullName }}</span>
          </div>

          <div class="space-y-1">
            <label class="text-[10px] uppercase font-bold text-white/30 ml-1">Email Address</label>
            <div class="relative">
              <Mail class="absolute left-4 top-1/2 -translate-y-1/2 text-white/20" :size="18" />
              <input v-model="email" type="email" placeholder="john@example.com"
                :class="errors.email ? 'border-red-500/50' : 'border-white/10'"
                class="w-full bg-white/5 border rounded-xl py-4 pl-12 pr-4 focus:outline-none focus:border-[#5cb83a] transition-colors">
            </div>
            <span class="text-red-400 text-[10px] ml-1">{{ errors.email }}</span>
          </div>

          <div class="space-y-1">
            <label class="text-[10px] uppercase font-bold text-white/30 ml-1">Phone Number (11 digits)</label>
            <div class="relative">
              <Phone class="absolute left-4 top-1/2 -translate-y-1/2 text-white/20" :size="18" />
              <input v-model="phone" type="tel" placeholder="08012345678"
                :class="errors.phone ? 'border-red-500/50' : 'border-white/10'"
                class="w-full bg-white/5 border rounded-xl py-4 pl-12 pr-4 focus:outline-none focus:border-[#5cb83a] transition-colors">
            </div>
            <span class="text-red-400 text-[10px] ml-1">{{ errors.phone }}</span>
          </div>

          <div class="space-y-1">
            <label class="text-[10px] uppercase font-bold text-white/30 ml-1">Password</label>
            <div class="relative">
              <Lock class="absolute left-4 top-1/2 -translate-y-1/2 text-white/20" :size="18" />
              <input v-model="password" type="password" placeholder="••••••••"
                :class="errors.password ? 'border-red-500/50' : 'border-white/10'"
                class="w-full bg-white/5 border rounded-xl py-4 pl-12 pr-4 focus:outline-none focus:border-[#5cb83a] transition-colors">
            </div>
            <span class="text-red-400 text-[10px] ml-1">{{ errors.password }}</span>
          </div>

          <button type="submit" :disabled="isSubmitting"
            class="w-full bg-[#2d7a18] hover:bg-[#3a9e20] hover:cursor-pointer text-white py-4 rounded-xl font-bold flex items-center justify-center gap-2 transition-all disabled:opacity-50">
            <span v-if="!isSubmitting">Sign up as a {{ role === 'buyer' ? 'Buyer' : 'Farmer' }} </span>
            <span v-else class="animate-pulse tracking-widest text-xs uppercase">Authenticating...</span>
            <ArrowRight v-if="!isSubmitting" :size="18" />
          </button>
        </form>

        <p class="text-center text-sm text-white/40">
          Already have an account? 
          <router-link to="/login" class="text-[#5cb83a] font-bold hover:underline">Sign In</router-link>
        </p>
      </div>
    </div>
  </div>
</template>