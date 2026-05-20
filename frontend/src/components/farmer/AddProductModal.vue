<script setup>
import { ref } from 'vue';
import api from '@/api/api';
import { X, Upload, BadgeCheck, Loader2, ScanEye, AlertTriangle, CheckCircle } from 'lucide-vue-next';

const props = defineProps(['isOpen']);
const emit = defineEmits(['close', 'refresh']);

const isSubmitting = ref(false);
const isScanning = ref(false);
const imageFile = ref(null);
const imagePreview = ref(null);

const scanResult = ref(null);
const scanComplete = ref(false);

const form = ref({
  name: '',
  description: '',
  price: '',
  available_quantity: 1,
  unit: 'Dozen'
});

const units = ['Dozen', 'Basket', '50kg Bag', '100kg Bag', 'Crate'];

const onFileChange = (e) => {
  const file = e.target.files[0];
  if (!file) return;
  imageFile.value = file;
  imagePreview.value = URL.createObjectURL(file);
  scanResult.value = null;
  scanComplete.value = false;
};

const handleListing = async () => {
  if (!imageFile.value || !form.value.name || !form.value.price) return;

  try {
    isScanning.value = true;

    const formData = new FormData();
    formData.append('name', form.value.name);
    formData.append('description', form.value.description || '');
    formData.append('price', parseFloat(form.value.price));
    formData.append('available_quantity', parseInt(form.value.available_quantity));
    formData.append('unit', form.value.unit);
    formData.append('image', imageFile.value);

    const response = await api.post('/products/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });

    scanResult.value = {
      is_healthy: !response.issue_type,
      disease_name: response.name || null,
      treatment: response.treatment || null,
      issue_type: response.issue_type || null
    };
    scanComplete.value = true;

    setTimeout(() => {
      emit('refresh');
      emit('close');
      resetForm();
    }, 2000);

  } catch (err) {
    console.error("Upload failed:", err);
    alert(err.detail || "Upload failed");
  } finally {
    isSubmitting.value = false;
    isScanning.value = false;
  }
};

const resetForm = () => {
  form.value = { name: '', description: '', price: '', available_quantity: 1, unit: 'Dozen' };
  imageFile.value = null;
  imagePreview.value = null;
  scanResult.value = null;
  scanComplete.value = false;
};
</script>

<template>
  <div v-if="isOpen" class="fixed inset-0 z-60 flex items-center justify-center p-4 bg-[#061209]/95 backdrop-blur-md">
    <div class="bg-[#0d2010] border border-white/10 w-full max-w-xl rounded-[2.5rem] p-8 md:p-10 relative shadow-2xl overflow-y-auto max-h-[95vh]">
      
      <button @click="$emit('close')" class="absolute top-8 right-8 text-white/20 hover:text-white transition-colors">
        <X :size="20" />
      </button>

      <div class="mb-8 text-center md:text-left">
        <h2 class="text-2xl font-serif text-[#f0ede4]">Upload Produce</h2>
        <p class="text-white/40 text-sm mt-1">Our AI will verify quality once you upload the photo.</p>
      </div>

      <form @submit.prevent="handleListing" class="space-y-6">
        <div class="space-y-2">
          <label class="text-[10px] uppercase tracking-widest text-white/30 font-bold ml-1">Product Image</label>
          <div 
            @click="$refs.fileInput.click()"
            class="group relative h-48 w-full border-2 border-dashed border-white/10 rounded-3xl flex flex-col items-center justify-center bg-white/5 cursor-pointer hover:border-[#5cb83a]/50 transition-all overflow-hidden"
          >
            <img v-if="imagePreview" :src="imagePreview" class="absolute inset-0 w-full h-full object-cover" />
            
            <div v-if="!imagePreview" class="flex flex-col items-center gap-2">
              <Upload class="text-white/20 group-hover:text-[#5cb83a] transition-colors" />
              <span class="text-xs text-white/40 font-medium">Click to upload photo</span>
            </div>

            <div v-if="isScanning" class="absolute inset-0 bg-[#061209]/80 backdrop-blur-sm flex flex-col items-center justify-center">
              <ScanEye class="text-[#5cb83a] animate-bounce mb-2" :size="32" />
              <div class="w-32 h-1 bg-white/10 rounded-full overflow-hidden">
                <div class="h-full bg-[#5cb83a] animate-[loading_2.5s_ease-in-out]"></div>
              </div>
              <span class="text-[10px] text-[#5cb83a] mt-2 uppercase font-bold tracking-widest">AI Quality Scan...</span>
            </div>
          </div>
          <input type="file" ref="fileInput" @change="onFileChange" class="hidden" accept="image/*" />

        <!-- Scan Result Display -->
        <div v-if="scanComplete" class="p-4 rounded-2xl border" :class="scanResult?.is_healthy ? 'bg-[#5cb83a]/10 border-[#5cb83a]/20' : 'bg-red-500/10 border-red-500/20'">
          <div class="flex items-start gap-3">
            <CheckCircle v-if="scanResult?.is_healthy" class="text-[#5cb83a] shrink-0 mt-0.5" :size="20" />
            <AlertTriangle v-else class="text-red-400 shrink-0 mt-0.5" :size="20" />
            <div>
              <p class="font-bold" :class="scanResult?.is_healthy ? 'text-[#5cb83a]' : 'text-red-400'">
                {{ scanResult?.is_healthy ? 'Product Verified - Healthy!' : 'Disease Detected' }}
              </p>
              <p v-if="!scanResult?.is_healthy && scanResult?.disease_name" class="text-sm text-red-300 mt-1">
                Issue: {{ scanResult.disease_name }}
              </p>
              <div v-if="!scanResult?.is_healthy && scanResult?.treatment" class="mt-3 p-3 bg-[#061209]/50 rounded-xl">
                <p class="text-[10px] text-white/40 uppercase font-bold mb-1">Recommended Treatment:</p>
                <p class="text-sm text-white/80">{{ scanResult.treatment }}</p>
              </div>
              <p v-if="!scanResult?.is_healthy" class="text-[10px] text-white/40 mt-2">
                This product will be flagged as unhealthy in the marketplace. Buyers will see this warning before purchasing.
              </p>
            </div>
          </div>
        </div>
        </div>

        <div class="space-y-4">
          <input v-model="form.name" type="text" placeholder="Produce Name (e.g. Fresh Cucumber)" 
                 class="w-full bg-white/5 border border-white/10 rounded-2xl py-4 px-6 outline-none focus:border-[#5cb83a] text-sm" required />
          
          <textarea v-model="form.description" placeholder="Description..." 
                    class="w-full bg-white/5 border border-white/10 rounded-2xl py-4 px-6 outline-none focus:border-[#5cb83a] text-sm resize-none"></textarea>
        </div>

        <div class="grid grid-cols-3 gap-3">
          <div class="col-span-1">
            <input v-model="form.price" type="number" placeholder="Price" 
                   class="w-full bg-white/5 border border-white/10 rounded-2xl py-4 px-6 outline-none focus:border-[#5cb83a] text-sm" required />
          </div>
          <div class="col-span-1">
            <input v-model="form.available_quantity" type="number" placeholder="Qty" 
                   class="w-full bg-white/5 border border-white/10 rounded-2xl py-4 px-6 outline-none focus:border-[#5cb83a] text-sm" required />
          </div>
          <div class="col-span-1">
            <select v-model="form.unit" class="w-full bg-white/5 border border-white/10 rounded-2xl py-4 px-6 outline-none focus:border-[#5cb83a] text-sm appearance-none">
              <option v-for="u in units" :key="u" :value="u">{{ u }}</option>
            </select>
          </div>
        </div>

        <button 
          type="submit" 
          :disabled="isSubmitting || isScanning"
          class="w-full bg-[#5cb83a] hover:bg-[#4ea131] text-[#061209] py-5 rounded-2xl font-bold flex items-center justify-center gap-2 transition-all disabled:opacity-30"
        >
          <template v-if="!isSubmitting && !isScanning">
            <BadgeCheck :size="20" /> Post Listing
          </template>
          <template v-else>
            <Loader2 class="animate-spin" :size="20" /> 
            {{ isScanning ? 'AI Verifying...' : 'Uploading...' }}
          </template>
        </button>
      </form>
    </div>
  </div>
</template>

<style scoped>
@keyframes loading {
  0% { width: 0%; }
  100% { width: 100%; }
}
</style>