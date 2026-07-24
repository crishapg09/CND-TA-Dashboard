import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
// base must match the GitHub Pages sub-path: https://<user>.github.io/<repo>/
export default defineConfig({
  base: '/Performance-Management-Dashboard/',
  plugins: [react()],
})
