<script setup>
import { ref, onMounted } from 'vue';
import { useForm, useField } from 'vee-validate';
import * as yup from 'yup';
import { 
  Plus, X, User, Mail, Phone, Lock, 
  Loader2, RefreshCw, ClipboardList, CheckCircle2 
} from 'lucide-vue-next';
import { createRider, getAllRiders, assignRider } from '../../api/api';
import RiderTable from './tables/RiderTable.vue';

// 1. States
const isModalOpen = ref(false);
const isAssignModalOpen = ref(false);
const ridersList = ref([]);
const isLoading = ref(true);
const currentPage = ref(1);
const totalPages = ref(1);


// 2. Fetch Logic
const fetchRiders = async (page = 1) => {
  isLoading.value = true;
  try {
    const data = await getAllRiders({ page, per_page: 20 });
    // Structure: { dispatch_riders: [], total_pages: X, page: X }
    ridersList.value = data.dispatch_riders || [];
    totalPages.value = data.total_pages || 1;
    currentPage.value = data.page || page;
  } catch (err) {
    console.error('Failed to fetch riders:', err);
  } finally {
    isLoading.value = false;
  }
};

const handlePageChange = (newPage) => {
  if (newPage >= 1 && newPage <= totalPages.value) {
    fetchRiders(newPage);
  }
};

onMounted(() => {
  fetchRiders();
});

// 3. Validation Schema for "Create Rider"
const createSchema = yup.object({
  full_name: yup.string().required('Full name is required').min(3, 'Name is too short'),
  email: yup.string().required('Email is required').email('Enter a valid email'),
  password: yup.string().required('Password is required').min(6, 'Min 6 characters'),
  phone_number: yup.string().required('Phone number is required'),
});

const createForm = useForm({
  validationSchema: createSchema,
});

const { value: full_name } = useField('full_name');
const { value: email } = useField('email');
const { value: password } = useField('password');
const { value: phone_number } = useField('phone_number');

const onCreateSubmit = createForm.handleSubmit(async (values) => {
  try {
    await createRider(values);
    await fetchRiders(currentPage.value); 
    isModalOpen.value = false;
    createForm.resetForm();
  } catch (err) {
    console.error('Submission Error:', err);
  }
});

// 4. Validation Schema for "Assign Rider"
const assignSchema = yup.object({
  order_id: yup.string().required('Order ID is required').uuid('Must be a valid UUID'),
  rider_id: yup.string().required('Rider ID is required').uuid('Must be a valid UUID'),
});

const assignForm = useForm({ 
  validationSchema: assignSchema 
});

const { value: order_id } = useField('order_id');
const { value: rider_id } = useField('rider_id');

const onAssignRider = assignForm.handleSubmit(async (values, { setErrors }) => {
  try {
    await assignRider(values);
    isAssignModalOpen.value = false;
    assignForm.resetForm();

  } catch (err) {
    // CAPTURE BACKEND ERROR: "Can only assign rider to paid orders"
    const errorMessage = err.detail || "Assignment failed";
    console.log(err)
    setErrors({
      order_id: errorMessage
    });
    console.error('Assignment Error:', err);
  }
});

const handleEditRider = (rider) => {
  console.log('Edit rider:', rider.id);
};

const handleDeleteRider = (id) => {
  console.log('Delete rider:', id);
};
</script>

<template>
  <div class="relative min-h-100">
    <div class="flex justify-between items-center mb-8">
      <div>
        <h1 class="text-2xl font-bold text-white">Dispatch Riders</h1>
        <p class="text-white/40 text-sm">Manage and monitor all active delivery personnel.</p>
      </div>
      
      <div class="flex gap-3">
        <button @click="fetchRiders(currentPage)" class="p-2 border border-white/10 rounded-lg hover:bg-white/5 transition-colors">
          <RefreshCw :size="20" :class="{ 'animate-spin': isLoading }" class="text-white/40" />
        </button>

        <button 
          @click="isModalOpen = true"
          class="bg-[#2d7a18] hover:bg-[#3a9e20] text-white px-4 py-2 rounded-lg flex items-center gap-2 transition-all font-semibold shadow-lg"
        >
          <Plus :size="18" />
          Create New Rider
        </button>
      </div>
    </div>

    <button 
      @click="isAssignModalOpen = true"
      class="bg-[#2d7a18] mb-6 hover:bg-[#3a9e20] text-white px-4 py-2 rounded-lg flex items-center gap-2 transition-all font-semibold shadow-lg"
    >
      <ClipboardList :size="16" />
      Assign Rider to Order
    </button>

    <div v-if="isLoading && ridersList.length === 0" class="flex flex-col items-center justify-center py-20">
        <Loader2 class="animate-spin text-[#5cb83a] mb-4" :size="40" />
        <p class="text-white/40">Loading fleet data...</p>
    </div>

    <RiderTable 
      v-else 
      :riders="ridersList"
      :currentPage="currentPage"
      :totalPages="totalPages"
      @changePage="handlePageChange"
      @edit="handleEditRider"
      @delete="handleDeleteRider"
    />

    <Transition name="fade">
      <div v-if="isModalOpen" class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm">
        <div class="bg-[#061209] border border-white/10 w-full max-w-md rounded-2xl shadow-2xl overflow-hidden">
          <div class="p-6 border-b border-white/10 flex justify-between items-center">
            <h3 class="text-xl font-bold text-white">Create Dispatch Rider</h3>
            <button @click="isModalOpen = false" class="text-white/40 hover:text-white transition-colors">
              <X :size="24" />
            </button>
          </div>

          <form @submit.prevent="onCreateSubmit" class="p-6 space-y-5">
             <div class="space-y-1.5">
              <label class="text-xs font-bold uppercase text-white/40">Full Name</label>
              <div class="relative">
                <User class="absolute left-3 top-1/2 -translate-y-1/2 text-white/20" :size="18" />
                <input v-model="full_name" type="text" placeholder="John Doe" 
                  class="w-full bg-white/5 border border-white/10 rounded-xl py-3 pl-10 pr-4 text-white outline-none focus:border-[#5cb83a]/50" />
              </div>
              <p v-if="createForm.errors.value.full_name" class="text-red-400 text-xs mt-1">{{ createForm.errors.value.full_name }}</p>
            </div>

            <div class="space-y-1.5">
              <label class="text-xs font-bold uppercase text-white/40">Email Address</label>
              <div class="relative">
                <Mail class="absolute left-3 top-1/2 -translate-y-1/2 text-white/20" :size="18" />
                <input v-model="email" type="email" placeholder="rider@farmpay.ng" 
                  class="w-full bg-white/5 border border-white/10 rounded-xl py-3 pl-10 pr-4 text-white outline-none focus:border-[#5cb83a]/50" />
              </div>
              <p v-if="createForm.errors.value.email" class="text-red-400 text-xs mt-1">{{ createForm.errors.value.email }}</p>
            </div>

            <div class="grid grid-cols-2 gap-4">
              <div class="space-y-1.5">
                <label class="text-xs font-bold uppercase text-white/40">Phone</label>
                <div class="relative">
                  <Phone class="absolute left-3 top-1/2 -translate-y-1/2 text-white/20" :size="16" />
                  <input v-model="phone_number" type="text" placeholder="080..." 
                    class="w-full bg-white/5 border border-white/10 rounded-xl py-3 pl-9 text-sm text-white outline-none focus:border-[#5cb83a]/50" />
                </div>
              </div>
              <div class="space-y-1.5">
                <label class="text-xs font-bold uppercase text-white/40">Password</label>
                <div class="relative">
                  <Lock class="absolute left-3 top-1/2 -translate-y-1/2 text-white/20" :size="16" />
                  <input v-model="password" type="password" placeholder="••••••" 
                    class="w-full bg-white/5 border border-white/10 rounded-xl py-3 pl-9 text-sm text-white outline-none focus:border-[#5cb83a]/50" />
                </div>
              </div>
            </div>

            <button 
              type="submit" 
              :disabled="createForm.isSubmitting.value"
              class="w-full bg-[#2d7a18] hover:bg-[#3a9e20] text-white py-4 rounded-xl font-bold flex items-center justify-center gap-2 transition-all disabled:opacity-50"
            >
              <Loader2 v-if="createForm.isSubmitting.value" class="animate-spin" :size="20" />
              {{ createForm.isSubmitting.value ? 'Registering...' : 'Create Account' }}
            </button>
          </form>
        </div>
      </div>
    </Transition>

    <Transition name="fade">
      <div v-if="isAssignModalOpen" class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm">
        <div class="bg-[#061209] border border-white/10 w-full max-w-md rounded-2xl shadow-2xl overflow-hidden">
          <div class="p-6 border-b border-white/10 flex justify-between items-center">
            <h3 class="text-xl font-bold text-white">Assign Task</h3>
            <button @click="isAssignModalOpen = false" class="text-white/40 hover:text-white">
              <X :size="24" />
            </button>
          </div>

          <form @submit.prevent="onAssignRider" class="p-6 space-y-6">
            <div class="space-y-1.5">
              <label class="text-[10px] font-bold uppercase tracking-[2px] text-white/30">Order UUID</label>
              <div class="relative">
                <ClipboardList class="absolute left-3 top-1/2 -translate-y-1/2 text-white/20" :size="18" />
                <input v-model="order_id" type="text" placeholder="UUID..." 
                  class="w-full bg-white/5 border border-white/10 rounded-xl py-3 pl-10 pr-4 text-white outline-none font-mono text-xs transition-all"
                  :class="{'border-red-500/50 bg-red-500/5': assignForm.errors.value.order_id, 'focus:border-[#5cb83a]/50': !assignForm.errors.value.order_id}" />
              </div>
              <p v-if="assignForm.errors.value.order_id" class="text-red-400 text-[10px] uppercase font-bold mt-1 tracking-wider">
                {{ assignForm.errors.value.order_id }}
              </p>
            </div>

            <div class="space-y-1.5">
              <label class="text-[10px] font-bold uppercase tracking-[2px] text-white/30">Rider UUID</label>
              <div class="relative">
                <User class="absolute left-3 top-1/2 -translate-y-1/2 text-white/20" :size="18" />
                <input v-model="rider_id" type="text" placeholder="UUID..." 
                  class="w-full bg-white/5 border border-white/10 rounded-xl py-3 pl-10 pr-4 text-white outline-none font-mono text-xs focus:border-[#5cb83a]/50"
                  :class="{'border-red-500/50 bg-red-500/5': assignForm.errors.value.rider_id}" />
              </div>
              <p v-if="assignForm.errors.value.rider_id" class="text-red-400 text-[10px] uppercase font-bold mt-1 tracking-wider">
                {{ assignForm.errors.value.rider_id }}
              </p>
            </div>

            <button 
              type="submit" 
              :disabled="assignForm.isSubmitting.value"
              class="w-full bg-[#2d7a18] hover:bg-[#3a9e20] text-white py-4 rounded-xl font-bold flex items-center justify-center gap-2 transition-all disabled:opacity-50"
            >
              <Loader2 v-if="assignForm.isSubmitting.value" class="animate-spin" :size="20" />
              <CheckCircle2 v-else :size="20" />
              {{ assignForm.isSubmitting.value ? 'Processing...' : 'Confirm Assignment' }}
            </button>
          </form>
        </div>
      </div>
    </Transition>
  </div>
</template>

<style scoped>
.fade-enter-active, .fade-leave-active { transition: opacity 0.3s ease; }
.fade-enter-from, .fade-leave-to { opacity: 0; }
</style>