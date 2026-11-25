import { NavLink, Outlet, useLocation, useNavigate } from "react-router-dom";
import {
  BookOpen,
  Brain,
  GitGraph,
  Home,
  MessageSquare,
  Route,
  Settings,
  Upload,
} from "lucide-react";
import { useSession } from "@/features/auth/session";
import { CommandPalette } from "./CommandPalette";
import { ThemeToggle } from "./ThemeToggle";
import { useState } from "react";
import { Button } from "@/shared/ui/Button";
import { apiFetch } from "@/api/client";

const LINKS = [
  { to: "/app", label: "Genome", icon: Home, end: true },
  { to: "/app/documents", label: "Documents", icon: Upload },
  { to: "/app/genome", label: "Graph", icon: GitGraph },
  { to: "/app/tutor", label: "Tutor", icon: MessageSquare },
  { to: "/app/mastery", label: "Mastery", icon: Brain },
  { to: "/app/path", label: "Path", icon: Route },
  { to: "/app/settings", label: "Settings", icon: Settings },
];

export function AppShell() {
  const user = useSession((s) => s.user);
  const location = useLocation();
  const navigate = useNavigate();
  const [cmd, setCmd] = useState(false);
  const crumbs = location.pathname.split("/").filter(Boolean);

  return (
    <div className="min-h-screen bg-canvas md:grid md:grid-cols-[240px_1fr]">
      <aside className="hidden border-r border-line bg-surface p-4 md:flex md:flex-col">
        <div className="font-display text-xl">MindGenome</div>
        <p className="mt-1 text-xs text-muted">AI that understands the learner</p>
        <nav className="mt-6 flex flex-col gap-1" aria-label="App">
          {LINKS.map((l) => (
            <NavLink
              key={l.to}
              to={l.to}
              end={l.end}
              className={({ isActive }) =>
                `flex items-center gap-2 rounded-control px-3 py-2 text-sm font-semibold ${
                  isActive ? "bg-helix/10 text-helix" : "text-muted hover:text-ink"
                }`
              }
            >
              <l.icon className="h-4 w-4" />
              {l.label}
            </NavLink>
          ))}
        </nav>
        <div className="mt-auto text-xs text-muted">
          <BookOpen className="mb-1 h-4 w-4" />
          Demo: {user?.display_name}
        </div>
      </aside>
      <div className="flex min-h-screen flex-col">
        <header className="flex items-center justify-between gap-3 border-b border-line bg-surface px-4 py-3">
          <nav aria-label="Breadcrumb" className="text-sm text-muted">
            {crumbs.map((c, i) => (
              <span key={c}>
                {i > 0 ? " / " : ""}
                <span className="text-ink">{c}</span>
              </span>
            ))}
          </nav>
          <div className="flex items-center gap-2">
            <Button variant="secondary" onClick={() => setCmd(true)} aria-keyshortcuts="Meta+K">
              Search ⌘K
            </Button>
            <ThemeToggle />
            <Button
              variant="ghost"
              onClick={async () => {
                const refresh = useSession.getState().refreshToken;
                try {
                  await apiFetch("/auth/logout", {
                    method: "POST",
                    body: JSON.stringify({ refresh_token: refresh }),
                  });
                } catch {
                  /* still clear */
                }
                useSession.getState().clear();
                navigate("/login");
              }}
            >
              Sign out
            </Button>
          </div>
        </header>
        <main className="flex-1 p-4 md:p-8">
          <Outlet />
        </main>
        <nav
          className="grid grid-cols-4 border-t border-line bg-surface md:hidden"
          aria-label="Mobile"
        >
          {LINKS.slice(0, 4).map((l) => (
            <NavLink
              key={l.to}
              to={l.to}
              end={l.end}
              className="flex flex-col items-center py-2 text-xs text-muted"
            >
              <l.icon className="h-4 w-4" />
              {l.label}
            </NavLink>
          ))}
        </nav>
      </div>
      <CommandPalette open={cmd} onOpenChange={setCmd} />
    </div>
  );
}
