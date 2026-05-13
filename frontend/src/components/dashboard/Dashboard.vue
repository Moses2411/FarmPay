<script setup>
import { Bell, Search } from 'lucide-vue-next';
import Sidebar from './SideBar.vue';
</script>

<template>
  <div class="flex min-h-screen bg-[#061209] text-[#f0ede4] font-sans">
    <!-- Sidebar -->
    <Sidebar />

    <!-- Main Content -->
    <div class="flex-1 flex flex-col">
      <!-- Header -->
      <!-- <header class="h-16 border-b border-white/10 flex items-center justify-between px-8 bg-[#061209]/50 backdrop-blur-md sticky top-0 z-10">
        <div class="flex items-center gap-4 bg-white/5 px-4 py-2 rounded-full border border-white/10 w-96">
          <Search :size="16" class="text-white/30" />
          <input 
            type="text" 
            placeholder="Search records..." 
            class="bg-transparent border-none outline-none text-sm w-full placeholder:text-white/20"
          />
        </div>

        <div class="flex items-center gap-6">
          <button class="relative text-white/60 hover:text-white">
            <Bell :size="20" />
            <span class="absolute -top-1 -right-1 w-2 h-2 bg-[#5cb83a] rounded-full"></span>
          </button>
          <div class="h-8 w-8 rounded-full bg-[#2d7a18] border border-white/20"></div>
        </div>
      </header> -->

      <!-- Viewport -->
      <main class="p-8">
        <router-view v-slot="{ Component }">
          <transition name="fade" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </main>
    </div>
  </div>
</template>

<style>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

/* Scrollbar Styling */
::-webkit-scrollbar {
  width: 6px;
}
::-webkit-scrollbar-track {
  background: #061209;
}
::-webkit-scrollbar-thumb {
  background: #2d7a18;
  border-radius: 10px;
}
</style>