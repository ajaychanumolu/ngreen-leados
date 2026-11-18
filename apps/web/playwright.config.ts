import { defineConfig } from "@playwright/test";

const ci = Boolean(process.env.CI);

export default defineConfig({
  testDir: "./e2e",
  timeout: 60_000,
  use: { baseURL: "http://localhost:3000" },
  webServer: [
    {
      command: "python -m uvicorn ngreen_api.main:app --app-dir services/api --port 8000",
      cwd: "../..",
      url: "http://127.0.0.1:8000/health",
      reuseExistingServer: !ci,
      timeout: 120_000,
      env: {
        DATABASE_URL: "sqlite:///./data/e2e.db",
        DEMO_AUTH_ENABLED: "true",
        SUPABASE_URL: "",
        SERPER_API_KEY: "",
        AI_PROVIDER: "mock",
        AI_API_KEY: "",
        VAPI_API_KEY: "",
        VOICE_LIVE_ENABLED: "false",
        VOICE_LEGAL_APPROVED: "false",
        LOCAL_JWT_SECRET: "e2e-only-secret",
      },
    },
    {
      command: "corepack pnpm dev --port 3000",
      url: "http://localhost:3000/login",
      reuseExistingServer: !ci,
      timeout: 120_000,
    },
  ],
});
