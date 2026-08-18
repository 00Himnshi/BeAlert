import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// GitHub Pages serves project websites from /repository-name/.
// The publish workflow supplies that folder name during its build.
export default defineConfig({
  plugins: [react()],
  base: process.env.VITE_BASE_PATH || "/"
});
