import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    react({
      babel: {
        plugins: [['babel-plugin-react-compiler']],
      },
    }),
  ],
  // @ts-expect-error Vitest config field
  test: {
    environment: 'jsdom',
    setupFiles: './src/test/setup.ts',
  },
})
