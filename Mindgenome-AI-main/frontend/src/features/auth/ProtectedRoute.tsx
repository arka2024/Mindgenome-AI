import { Navigate, Outlet, useLocation } from "react-router-dom";
import { useSession } from "./session";
import { useQuery } from "@tanstack/react-query";
import { apiFetch } from "@/api/client";
import type { User } from "@/api/schemas";
import { qk } from "@/shared/lib/queryKeys";
import { Skeleton } from "@/shared/ui/Skeleton";

export function ProtectedRoute() {
  const access = useSession((s) => s.accessToken);
  const refresh = useSession((s) => s.refreshToken);
  const setUser = useSession((s) => s.setUser);
  const location = useLocation();

  const me = useQuery({
    queryKey: qk.me,
    enabled: Boolean(access || refresh),
    queryFn: async () => {
      const user = await apiFetch<User>("/auth/me");
      setUser(user);
      return user;
    },
    retry: false,
  });

  if (!access && !refresh) {
    return <Navigate to="/login" replace state={{ from: location.pathname }} />;
  }
  if (me.isLoading) {
    return (
      <div className="p-8">
        <Skeleton className="h-10 w-48" />
        <Skeleton className="mt-4 h-64 w-full" />
      </div>
    );
  }
  if (me.isError) {
    return <Navigate to="/login" replace />;
  }
  return <Outlet />;
}
