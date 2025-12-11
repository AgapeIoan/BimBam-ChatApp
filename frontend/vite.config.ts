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
    globals: true,
    environment: "jsdom",
    coverage: {
      provider: "v8",      
      reporter: ["text", "html", "lcov"],
      reportsDirectory: "./coverage",

      include: ["src/**/*.ts", "src/**/*.tsx"],
      exclude: [
        "src/**/*.test.ts",
        "src/**/*.spec.ts",
        "node_modules/",
        "src/tests/",
        "src/types/",
        "src/components/figma/**",
        "src/components/ui/**",
        "src/mock_data/**",
        "src/test/setup.ts",
        "src/App.tsx",
        "src/main.tsx",
        "src/api.ts",
      ],

      lines: 80,
      functions: 80,
      branches: 70,
      statements: 80,
    },
  },
});