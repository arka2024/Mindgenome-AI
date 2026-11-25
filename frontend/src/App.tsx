import { Navigate, Route, Routes } from "react-router-dom";
import { Providers } from "@/app/providers";
import { AppShell } from "@/app/shell/AppShell";
import { ProtectedRoute } from "@/features/auth/ProtectedRoute";
import { ForgotPage, LoginPage, RegisterPage } from "@/features/auth/AuthPages";
import { DashboardPage } from "@/features/dashboard/DashboardPage";
import { DocumentDetailPage } from "@/features/documents/DocumentDetailPage";
import { DocumentsPage } from "@/features/documents/DocumentsPage";
import { GenomeGraphPage } from "@/features/graph/GenomeGraphPage";
import { TutorPage } from "@/features/tutor/TutorPage";
import { LearningSessionPage } from "@/features/learning/LearningSessionPage";
import { QuizPage } from "@/features/quiz/QuizPage";
import { MasteryPage } from "@/features/mastery/MasteryPage";
import { LearningPathPage } from "@/features/path/LearningPathPage";
import { SettingsPage } from "@/features/settings/SettingsPage";
import { LandingPage } from "@/features/marketing/LandingPage";
import { AboutPage, PricingPage, StyleGuidePage } from "@/features/marketing/SimplePages";

function AppRoutes() {
  return (
    <Routes>
      <Route path="/" element={<LandingPage />} />
      <Route path="/pricing" element={<PricingPage />} />
      <Route path="/about" element={<AboutPage />} />
      <Route path="/styleguide" element={<StyleGuidePage />} />
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />
      <Route path="/forgot-password" element={<ForgotPage />} />
      <Route element={<ProtectedRoute />}>
        <Route element={<AppShell />}>
          <Route path="/app" element={<DashboardPage />} />
          <Route path="/app/documents" element={<DocumentsPage />} />
          <Route path="/app/documents/:id" element={<DocumentDetailPage />} />
          <Route path="/app/genome" element={<GenomeGraphPage />} />
          <Route path="/app/tutor" element={<TutorPage />} />
          <Route path="/app/learn/:id" element={<LearningSessionPage />} />
          <Route path="/app/quiz/:id" element={<QuizPage />} />
          <Route path="/app/mastery" element={<MasteryPage />} />
          <Route path="/app/path" element={<LearningPathPage />} />
          <Route path="/app/settings" element={<SettingsPage />} />
        </Route>
      </Route>
      <Route path="/dashboard" element={<Navigate to="/app" replace />} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

function App() {
  return (
    <Providers>
      <AppRoutes />
    </Providers>
  );
}

export default App;
