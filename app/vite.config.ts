import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
// base must match the GitHub Pages sub-path this app is served from. The repo
// root serves the CND & Climate TA dashboard; this app is published one level
// down, at https://<user>.github.io/<repo>/performance/ (see deploy-pages.yml).
export default defineConfig({
  base: '/CND-TA-Dashboard/performance/',
  plugins: [react()],
})
