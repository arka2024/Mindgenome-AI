import { useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { zodResolver } from "./zodResolver";
import { Link, useNavigate } from "react-router-dom";
import { apiFetch, ApiError } from "@/api/client";
import type { TokenPair } from "@/api/schemas";
import { useSession } from "./session";
import { Button } from "@/shared/ui/Button";
import { Field, Input } from "@/shared/ui/Input";
import { Card } from "@/shared/ui/Card";
import { DEMO_EMAIL, DEMO_PASSWORD } from "@/mocks/seed";
import { ArrowLeft, CheckCircle2, Eye, EyeOff, Lock, Mail, Sparkles, User } from "lucide-react";

const loginSchema = z.object({
  email: z.string().email("Please enter a valid email address"),
  password: z.string().min(1, "Password is required"),
});

const registerSchema = z.object({
  display_name: z.string().min(1, "Name is required").max(80),
  email: z.string().email("Please enter a valid email address"),
  password: z.string().min(12, "Password must be at least 12 characters"),
});

const forgotSchema = z.object({
  email: z.string().email("Please enter a valid email address"),
});

export function LoginPage() {
  const navigate = useNavigate();
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [showPassword, setShowPassword] = useState(false);
  const [isDemoLoading, setIsDemoLoading] = useState(false);

  const form = useForm({
    resolver: zodResolver(loginSchema),
    defaultValues: { email: DEMO_EMAIL, password: DEMO_PASSWORD },
  });

  const onSubmit = async (values: z.infer<typeof loginSchema>) => {
    setErrorMsg(null);
    try {
      const tokens = await apiFetch<TokenPair>("/auth/login", {
        method: "POST",
        body: JSON.stringify(values),
      });
      useSession.getState().setTokens(tokens.access_token, tokens.refresh_token, tokens.expires_in);
      navigate("/app");
    } catch (e) {
      setErrorMsg(e instanceof ApiError ? e.message : "Invalid email or password.");
    }
  };

  const handleQuickDemo = async () => {
    setIsDemoLoading(true);
    setErrorMsg(null);
    try {
      const tokens = await apiFetch<TokenPair>("/auth/login", {
        method: "POST",
        body: JSON.stringify({ email: DEMO_EMAIL, password: DEMO_PASSWORD }),
      });
      useSession.getState().setTokens(tokens.access_token, tokens.refresh_token, tokens.expires_in);
      navigate("/app");
    } catch (e) {
      setErrorMsg(e instanceof ApiError ? e.message : "Demo sign in failed.");
    } finally {
      setIsDemoLoading(false);
    }
  };

  return (
    <AuthFrame
      title="Welcome back"
      subtitle="Sign in to your personal knowledge genome"
    >
      <div className="mb-5 rounded-control border border-helix/30 bg-helix/5 p-3.5">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-1.5 text-xs font-semibold text-helix">
            <Sparkles className="h-3.5 w-3.5" />
            <span>Interactive Demo Ready</span>
          </div>
          <span className="text-[10px] font-mono text-muted">Prefilled</span>
        </div>
        <p className="mt-1 text-xs text-muted">
          Click below to instantly access the pre-seeded Machine Learning curriculum demo.
        </p>
        <Button
          type="button"
          variant="secondary"
          className="mt-2.5 w-full text-xs font-medium border-helix/40 hover:bg-helix/10"
          onClick={handleQuickDemo}
          disabled={isDemoLoading}
        >
          {isDemoLoading ? "Signing in..." : "Instant Demo Sign-In"}
        </Button>
      </div>

      <div className="relative mb-5 flex items-center justify-center text-xs">
        <div className="w-full border-t border-line" />
        <span className="absolute bg-surface px-2 text-muted">or continue with credentials</span>
      </div>

      <form className="space-y-4" onSubmit={form.handleSubmit(onSubmit)}>
        <Field label="Email" error={form.formState.errors.email?.message}>
          <div className="relative">
            <Input
              type="email"
              autoComplete="username"
              placeholder="you@domain.edu"
              className="pl-9"
              {...form.register("email")}
            />
            <Mail className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted pointer-events-none" />
          </div>
        </Field>

        <Field label="Password" error={form.formState.errors.password?.message}>
          <div className="relative">
            <Input
              type={showPassword ? "text" : "password"}
              autoComplete="current-password"
              className="pl-9 pr-10"
              {...form.register("password")}
            />
            <Lock className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted pointer-events-none" />
            <button
              type="button"
              className="absolute right-3 top-1/2 -translate-y-1/2 text-muted hover:text-ink"
              onClick={() => setShowPassword(!showPassword)}
              aria-label={showPassword ? "Hide password" : "Show password"}
            >
              {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
            </button>
          </div>
        </Field>

        {errorMsg ? (
          <div className="rounded-control border border-danger/40 bg-danger/10 p-2.5 text-xs text-danger" role="alert">
            {errorMsg}
          </div>
        ) : null}

        <Button
          type="submit"
          className="w-full font-semibold"
          disabled={form.formState.isSubmitting}
        >
          {form.formState.isSubmitting ? "Authenticating..." : "Sign In"}
        </Button>
      </form>

      <div className="mt-5 flex items-center justify-between text-xs text-muted">
        <Link to="/forgot-password" className="hover:text-helix underline underline-offset-2">
          Forgot password?
        </Link>
        <Link to="/register" className="hover:text-helix font-semibold text-ink">
          Create an account
        </Link>
      </div>
    </AuthFrame>
  );
}

export function RegisterPage() {
  const navigate = useNavigate();
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [showPassword, setShowPassword] = useState(false);

  const form = useForm({
    resolver: zodResolver(registerSchema),
    defaultValues: { display_name: "", email: "", password: "" },
  });

  const onSubmit = async (values: z.infer<typeof registerSchema>) => {
    setErrorMsg(null);
    try {
      const tokens = await apiFetch<TokenPair>("/auth/register", {
        method: "POST",
        body: JSON.stringify(values),
      });
      useSession.getState().setTokens(tokens.access_token, tokens.refresh_token, tokens.expires_in);
      navigate("/app");
    } catch (e) {
      setErrorMsg(e instanceof ApiError ? e.message : "Registration failed. Please try again.");
    }
  };

  const prefillSample = () => {
    form.setValue("display_name", "Alex Rivera");
    form.setValue("email", `learner_${Math.floor(Math.random() * 900 + 100)}@mit.edu`);
    form.setValue("password", "MindGenome2026!Secure");
  };

  return (
    <AuthFrame
      title="Create your genome"
      subtitle="Start building an adaptive, graph-augmented knowledge base"
    >
      <div className="mb-4 flex items-center justify-between">
        <span className="text-xs text-muted">Want to test quickly?</span>
        <button
          type="button"
          onClick={prefillSample}
          className="text-xs font-semibold text-helix hover:underline"
        >
          Prefill sample details
        </button>
      </div>

      <form className="space-y-4" onSubmit={form.handleSubmit(onSubmit)}>
        <Field label="Full Name" error={form.formState.errors.display_name?.message}>
          <div className="relative">
            <Input
              autoComplete="name"
              placeholder="Alex Rivera"
              className="pl-9"
              {...form.register("display_name")}
            />
            <User className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted pointer-events-none" />
          </div>
        </Field>

        <Field label="Email" error={form.formState.errors.email?.message}>
          <div className="relative">
            <Input
              type="email"
              autoComplete="email"
              placeholder="alex@institution.edu"
              className="pl-9"
              {...form.register("email")}
            />
            <Mail className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted pointer-events-none" />
          </div>
        </Field>

        <Field label="Password (min. 12 characters)" error={form.formState.errors.password?.message}>
          <div className="relative">
            <Input
              type={showPassword ? "text" : "password"}
              autoComplete="new-password"
              placeholder="••••••••••••"
              className="pl-9 pr-10"
              {...form.register("password")}
            />
            <Lock className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted pointer-events-none" />
            <button
              type="button"
              className="absolute right-3 top-1/2 -translate-y-1/2 text-muted hover:text-ink"
              onClick={() => setShowPassword(!showPassword)}
              aria-label={showPassword ? "Hide password" : "Show password"}
            >
              {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
            </button>
          </div>
        </Field>

        {errorMsg ? (
          <div className="rounded-control border border-danger/40 bg-danger/10 p-2.5 text-xs text-danger" role="alert">
            {errorMsg}
          </div>
        ) : null}

        <Button
          type="submit"
          className="w-full font-semibold"
          disabled={form.formState.isSubmitting}
        >
          {form.formState.isSubmitting ? "Creating Genome..." : "Create Account"}
        </Button>
      </form>

      <div className="mt-5 text-center text-xs text-muted">
        Already have a genome?{" "}
        <Link to="/login" className="font-semibold text-ink hover:text-helix underline underline-offset-2">
          Sign in
        </Link>
      </div>
    </AuthFrame>
  );
}

export function ForgotPage() {
  const [successMsg, setSuccessMsg] = useState<string | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const form = useForm({
    resolver: zodResolver(forgotSchema),
    defaultValues: { email: "" },
  });

  const onSubmit = async (values: z.infer<typeof forgotSchema>) => {
    setErrorMsg(null);
    try {
      const res = await apiFetch<{ message: string }>("/auth/forgot", {
        method: "POST",
        body: JSON.stringify(values),
      });
      setSuccessMsg(res.message);
    } catch (e) {
      setErrorMsg(e instanceof ApiError ? e.message : "Failed to send reset link.");
    }
  };

  return (
    <AuthFrame
      title="Reset Password"
      subtitle="Enter your email to receive a password recovery link"
    >
      {successMsg ? (
        <div className="space-y-4 rounded-control border border-helix/30 bg-helix/10 p-4 text-center">
          <CheckCircle2 className="mx-auto h-8 w-8 text-helix" />
          <p className="text-sm font-semibold text-ink">{successMsg}</p>
          <p className="text-xs text-muted">
            Check your inbox for a password reset confirmation link.
          </p>
          <Link to="/login" className="block pt-2">
            <Button variant="secondary" className="w-full text-xs">
              Back to Sign In
            </Button>
          </Link>
        </div>
      ) : (
        <form className="space-y-4" onSubmit={form.handleSubmit(onSubmit)}>
          <Field label="Email" error={form.formState.errors.email?.message}>
            <div className="relative">
              <Input
                type="email"
                autoComplete="email"
                placeholder="you@domain.edu"
                className="pl-9"
                {...form.register("email")}
              />
              <Mail className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted pointer-events-none" />
            </div>
          </Field>

          {errorMsg ? (
            <div className="rounded-control border border-danger/40 bg-danger/10 p-2.5 text-xs text-danger" role="alert">
              {errorMsg}
            </div>
          ) : null}

          <Button
            type="submit"
            className="w-full font-semibold"
            disabled={form.formState.isSubmitting}
          >
            {form.formState.isSubmitting ? "Sending Link..." : "Send Reset Link"}
          </Button>

          <div className="text-center">
            <Link to="/login" className="text-xs text-muted hover:text-ink">
              Back to Sign In
            </Link>
          </div>
        </form>
      )}
    </AuthFrame>
  );
}

function AuthFrame({
  title,
  subtitle,
  children,
}: {
  title: string;
  subtitle: string;
  children: React.ReactNode;
}) {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-canvas px-4 py-12 transition-colors duration-200">
      <Link
        to="/"
        className="mb-8 inline-flex items-center gap-1.5 text-xs font-semibold text-muted hover:text-ink"
      >
        <ArrowLeft className="h-3.5 w-3.5" /> Back to MindGenome Home
      </Link>

      <Card className="w-full max-w-md p-6 sm:p-8 border border-line shadow-card">
        <div className="mb-6 flex items-center gap-2.5">
          <div className="flex h-7 w-7 items-center justify-center rounded-control bg-helix text-white font-bold font-display text-sm">
            M
          </div>
          <span className="font-display text-lg font-bold">MindGenome AI</span>
        </div>

        <h1 className="font-display text-2xl font-bold sm:text-3xl">{title}</h1>
        <p className="mt-1 mb-6 text-xs text-muted leading-relaxed">{subtitle}</p>

        {children}
      </Card>

      <div className="mt-8 text-center text-xs text-muted">
        Protected by session refresh tokens & secure memory auth.
      </div>
    </div>
  );
}
