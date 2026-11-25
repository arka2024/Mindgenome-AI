import { create } from "zustand";
import type { User } from "@/api/schemas";
import { env } from "@/shared/lib/env";

const REFRESH_KEY = "mg.refresh";
const THEME_KEY = "mg.theme";
const FEEDBACK_KEY = "mg.quizFeedback";

type SessionState = {
  accessToken: string | null;
  refreshToken: string | null;
  user: User | null;
  theme: "light" | "dark";
  quizFeedback: "immediate" | "end";
  setTokens: (access: string, refresh: string, _expiresIn: number) => void;
  setUser: (user: User | null) => void;
  setTheme: (theme: "light" | "dark") => void;
  setQuizFeedback: (mode: "immediate" | "end") => void;
  clear: () => void;
};

function readRefresh(): string | null {
  if (env.authCookie) return null;
  try {
    return sessionStorage.getItem(REFRESH_KEY);
  } catch {
    return null;
  }
}

export const useSession = create<SessionState>((set) => ({
  accessToken: null,
  refreshToken: readRefresh(),
  user: null,
  theme: (localStorage.getItem(THEME_KEY) as "light" | "dark") || "light",
  quizFeedback: (localStorage.getItem(FEEDBACK_KEY) as "immediate" | "end") || "immediate",
  setTokens: (access, refresh) => {
    if (!env.authCookie) sessionStorage.setItem(REFRESH_KEY, refresh);
    set({ accessToken: access, refreshToken: refresh });
  },
  setUser: (user) => set({ user }),
  setTheme: (theme) => {
    localStorage.setItem(THEME_KEY, theme);
    document.documentElement.classList.toggle("dark", theme === "dark");
    set({ theme });
  },
  setQuizFeedback: (mode) => {
    localStorage.setItem(FEEDBACK_KEY, mode);
    set({ quizFeedback: mode });
  },
  clear: () => {
    sessionStorage.removeItem(REFRESH_KEY);
    set({ accessToken: null, refreshToken: null, user: null });
  },
}));

export function applyStoredTheme(): void {
  const theme = useSession.getState().theme;
  document.documentElement.classList.toggle("dark", theme === "dark");
}
