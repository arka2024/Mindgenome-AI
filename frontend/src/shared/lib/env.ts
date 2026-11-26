const configuredApiBaseUrl = import.meta.env.VITE_API_BASE_URL?.trim();
const productionApiBaseUrl = "https://mindgenome-ai-4.onrender.com/api/v1";
const productionApiOverride = configuredApiBaseUrl?.startsWith("https://")
  ? configuredApiBaseUrl
  : undefined;

export const env = {
  useMocks: import.meta.env.VITE_USE_MOCKS !== "false",
  apiBaseUrl: import.meta.env.PROD
    ? productionApiOverride ?? productionApiBaseUrl
    : configuredApiBaseUrl || "/api/v1",
  authCookie: import.meta.env.VITE_AUTH_COOKIE === "true",
  appName: import.meta.env.VITE_APP_NAME ?? "MindGenome AI",
};
