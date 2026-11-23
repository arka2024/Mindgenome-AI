import { Moon, Sun } from "lucide-react";
import { useSession } from "@/features/auth/session";
import { Button } from "@/shared/ui/Button";

export function ThemeToggle() {
  const theme = useSession((s) => s.theme);
  const setTheme = useSession((s) => s.setTheme);
  const next = theme === "dark" ? "light" : "dark";
  return (
    <Button
      variant="ghost"
      aria-label={`Switch to ${next} theme`}
      onClick={() => setTheme(next)}
    >
      {theme === "dark" ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
    </Button>
  );
}
