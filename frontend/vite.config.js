import { fileURLToPath, URL } from "node:url";
import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";
// 1. Add the missing TailwindCSS import
import tailwindcss from "@tailwindcss/vite";

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    vue(),
    tailwindcss(), // 2. Now this function call will work correctly
  ],
  resolve: {
    alias: {
      // This tells Vite: whenever you see '@', look in the 'src' folder
      "@": fileURLToPath(new URL("./src", import.meta.url)),
    },
  },
});
