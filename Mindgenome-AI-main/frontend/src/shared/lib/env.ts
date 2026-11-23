export const env = {
  useMocks: import.meta.env.VITE_USE_MOCKS !== "false",
  apiBaseUrl: import.meta.env.VITE_API_BASE_URL ?? "/api/v1",
  authCookie: import.meta.env.VITE_AUTH_COOKIE === "true",
  appName: import.meta.env.VITE_APP_NAME ?? "MindGenome AI",
};
