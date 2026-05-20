<script setup>
import { ref, onMounted, computed } from 'vue';
import { getProductReviews, createReview } from '@/api/api';
import { Star, Loader2, Send, X, MessageSquare } from 'lucide-vue-next';

const props = defineProps({
  productId: {
    type: String,
    required: true
  }
});

const emit = defineEmits(['close']);

const reviews = ref([]);
const isLoading = ref(true);
const isSubmitting = ref(false);
const showForm = ref(false);
const newReview = ref({
  rating: 5,
  comment: ''
});

const fetchReviews = async () => {
  isLoading.value = true;
  try {
    const response = await getProductReviews(props.productId);
    reviews.value = response.data || response;
  } catch (err) {
    console.error("Failed to load reviews:", err);
  } finally {
    isLoading.value = false;
  }
};

const submitReview = async () => {
  if (!newReview.value.comment.trim()) return;
  
  isSubmitting.value = true;
  try {
    await createReview({
      product_id: props.productId,
      rating: newReview.value.rating,
      comment: newReview.value.comment
    });
    newReview.value = { rating: 5, comment: '' };
    showForm.value = false;
    await fetchReviews();
  } catch (err) {
    console.error("Failed to submit review:", err);
    alert(err.detail || "Failed to submit review");
  } finally {
    isSubmitting.value = false;
  }
};

const averageRating = computed(() => {
  if (reviews.value.length === 0) return 0;
  const sum = reviews.value.reduce((acc, r) => acc + (r.rating || 0), 0);
  return (sum / reviews.value.length).toFixed(1);
});

const ratingCounts = computed(() => {
  const counts = { 5: 0, 4: 0, 3: 0, 2: 0, 1: 0 };
  reviews.value.forEach(r => {
    const rating = Math.round(r.rating || 0);
    if (counts[rating] !== undefined) counts[rating]++;
  });
  return counts;
});

const formatDate = (dateStr) => {
  if (!dateStr) return '';
  const date = new Date(dateStr);
  return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
};

onMounted(fetchReviews);
</script>

<template>
  <div class="bg-[#0d2010] border border-white/10 rounded-3xl p-6 max-h-[80vh] overflow-y-auto">
    <div class="flex justify-between items-center mb-6">
      <h3 class="text-lg font-serif">Customer Reviews</h3>
      <button v-if="!showForm" @click="showForm = true" class="text-[10px] uppercase font-bold text-[#5cb83a] hover:underline">
        Write Review
      </button>
    </div>

    <!-- Rating Summary -->
    <div v-if="reviews.length > 0" class="flex items-center gap-6 mb-8 pb-6 border-b border-white/5">
      <div class="text-center">
        <p class="text-4xl font-serif text-[#5cb83a]">{{ averageRating }}</p>
        <div class="flex gap-0.5 justify-center my-2">
          <Star v-for="i in 5" :key="i" :size="14" :class="i <= Math.round(averageRating) ? 'text-amber-400 fill-amber-400' : 'text-white/20'" />
        </div>
        <p class="text-[10px] text-white/30">{{ reviews.length }} reviews</p>
      </div>
      
      <div class="flex-1 space-y-1.5">
        <div v-for="star in [5, 4, 3, 2, 1]" :key="star" class="flex items-center gap-2">
          <span class="text-[10px] text-white/40 w-3">{{ star }}</span>
          <Star :size="12" class="text-amber-400 fill-amber-400" />
          <div class="flex-1 h-1.5 bg-white/10 rounded-full overflow-hidden">
            <div 
              class="h-full bg-amber-400 rounded-full transition-all"
              :style="{ width: `${(ratingCounts[star] / reviews.length) * 100}%` }"
            ></div>
          </div>
          <span class="text-[10px] text-white/30 w-6">{{ ratingCounts[star] }}</span>
        </div>
      </div>
    </div>

    <!-- Review Form -->
    <div v-if="showForm" class="mb-6 p-5 bg-white/5 border border-white/10 rounded-2xl">
      <div class="flex justify-between items-center mb-4">
        <span class="text-[10px] uppercase font-bold text-white/40">Your Review</span>
        <button @click="showForm = false" class="text-white/30 hover:text-white">
          <X :size="18" />
        </button>
      </div>
      
      <div class="flex items-center gap-2 mb-4">
        <span class="text-[10px] text-white/40">Rating:</span>
        <button 
          v-for="star in 5" 
          :key="star"
          @click="newReview.rating = star"
          class="transition-transform hover:scale-110"
        >
          <Star 
            :size="24" 
            :class="star <= newReview.rating ? 'text-amber-400 fill-amber-400' : 'text-white/20'"
          />
        </button>
      </div>

      <textarea 
        v-model="newReview.comment"
        placeholder="Share your experience with this product..."
        rows="3"
        class="w-full bg-white/5 border border-white/10 rounded-xl p-3 text-sm outline-none focus:border-[#5cb83a] transition-all resize-none"
      ></textarea>

      <button 
        @click="submitReview"
        :disabled="isSubmitting || !newReview.comment.trim()"
        class="mt-4 w-full bg-[#5cb83a] text-[#061209] py-3 rounded-xl font-bold text-xs uppercase tracking-widest flex items-center justify-center gap-2 hover:bg-[#4da330] transition-all disabled:opacity-30"
      >
        <Loader2 v-if="isSubmitting" class="animate-spin" :size="16" />
        <Send v-else :size="16" />
        Submit Review
      </button>
    </div>

    <!-- Reviews List -->
    <div v-if="isLoading" class="flex justify-center py-8">
      <Loader2 class="animate-spin text-[#5cb83a]" :size="24" />
    </div>

    <div v-else-if="reviews.length === 0" class="text-center py-8">
      <MessageSquare class="mx-auto mb-3 text-white/10" :size="32" />
      <p class="text-white/30 text-sm">No reviews yet</p>
      <p class="text-white/20 text-[10px] mt-1">Be the first to review this product</p>
    </div>

    <div v-else class="space-y-5">
      <div v-for="review in reviews" :key="review.id" class="pb-5 border-b border-white/5 last:border-0">
        <div class="flex justify-between items-start mb-2">
          <div class="flex items-center gap-2">
            <div class="w-8 h-8 rounded-full bg-[#5cb83a]/20 flex items-center justify-center text-[#5cb83a] text-xs font-bold">
              {{ (review.buyer?.full_name || 'B')[0].toUpperCase() }}
            </div>
            <div>
              <p class="text-xs font-bold text-white/80">{{ review.buyer?.full_name || 'Buyer' }}</p>
              <p class="text-[10px] text-white/30">{{ formatDate(review.created_at) }}</p>
            </div>
          </div>
          <div class="flex gap-0.5">
            <Star v-for="i in 5" :key="i" :size="12" :class="i <= (review.rating || 0) ? 'text-amber-400 fill-amber-400' : 'text-white/20'" />
          </div>
        </div>
        <p class="text-sm text-white/50 leading-relaxed">{{ review.comment }}</p>
      </div>
    </div>
  </div>
</template>