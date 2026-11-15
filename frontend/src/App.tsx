import React, { Suspense } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import { ThemeProvider } from './contexts/ThemeContext';

// Layouts (rendered synchronously so shell/navigation is immediate)
import { MainLayout } from './layouts/MainLayout';
import { AuthLayout } from './layouts/AuthLayout';
import { LearningLayout } from './layouts/LearningLayout';
import { LoadingSpinner } from './components/ui/LoadingSpinner';
import { RouteErrorBoundary } from './components/ui/RouteErrorBoundary';

// Route-level Lazy-Loaded Pages
const Landing = React.lazy(() => import('./pages/Landing').then((m) => ({ default: m.Landing })));
const Login = React.lazy(() => import('./pages/Login').then((m) => ({ default: m.Login })));
const Register = React.lazy(() => import('./pages/Register').then((m) => ({ default: m.Register })));
const Dashboard = React.lazy(() => import('./pages/Dashboard').then((m) => ({ default: m.Dashboard })));
const Subjects = React.lazy(() => import('./pages/Subjects').then((m) => ({ default: m.Subjects })));
const CourseDetail = React.lazy(() => import('./pages/CourseDetail').then((m) => ({ default: m.CourseDetail })));
const Lesson = React.lazy(() => import('./pages/Lesson').then((m) => ({ default: m.Lesson })));
const AITutor = React.lazy(() => import('./pages/AITutor').then((m) => ({ default: m.AITutor })));
const Progress = React.lazy(() => import('./pages/Progress').then((m) => ({ default: m.Progress })));
const QuickAssessment = React.lazy(() => import('./pages/QuickAssessment').then((m) => ({ default: m.QuickAssessment })));
const CollegeSimulator = React.lazy(() => import('./pages/CollegeSimulator').then((m) => ({ default: m.CollegeSimulator })));
const StudyPlan = React.lazy(() => import('./pages/StudyPlan').then((m) => ({ default: m.StudyPlan })));
const Profile = React.lazy(() => import('./pages/Profile').then((m) => ({ default: m.Profile })));
const Admin = React.lazy(() => import('./pages/Admin').then((m) => ({ default: m.Admin })));
const NotFound = React.lazy(() => import('./pages/NotFound').then((m) => ({ default: m.NotFound })));

const PageLoadingFallback: React.FC = () => (
  <div className="min-h-[50vh] flex flex-col items-center justify-center p-8 gap-3">
    <LoadingSpinner size="lg" />
    <span className="text-xs text-slate-400 dark:text-slate-500 font-medium">Loading view...</span>
  </div>
);

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
});

const ProtectedRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50 dark:bg-slate-950">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return <>{children}</>;
};

const AdminRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { user, isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50 dark:bg-slate-950">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  if (!isAuthenticated || user?.role !== 'admin') {
    return <Navigate to="/dashboard" replace />;
  }

  return <>{children}</>;
};

export const App: React.FC = () => {
  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider>
        <AuthProvider>
          <BrowserRouter>
            <RouteErrorBoundary>
              <Suspense fallback={<PageLoadingFallback />}>
                <Routes>
                  {/* Public Landing */}
                  <Route path="/" element={<Landing />} />

                  {/* Auth routes */}
                  <Route element={<AuthLayout />}>
                    <Route path="/login" element={<Login />} />
                    <Route path="/register" element={<Register />} />
                  </Route>

                  {/* Distraction-free interactive learning route */}
                  <Route
                    element={
                      <ProtectedRoute>
                        <LearningLayout />
                      </ProtectedRoute>
                    }
                  >
                    <Route path="/lessons/:id" element={<Lesson />} />
                  </Route>

                  {/* Protected Portal Routes */}
                  <Route
                    element={
                      <ProtectedRoute>
                        <MainLayout />
                      </ProtectedRoute>
                    }
                  >
                    <Route path="/dashboard" element={<Dashboard />} />
                    <Route path="/quick-assessment" element={<QuickAssessment />} />
                    <Route path="/subjects" element={<Subjects />} />
                    <Route path="/courses/:id" element={<CourseDetail />} />
                    <Route path="/ai-tutor" element={<AITutor />} />
                    <Route path="/progress" element={<Progress />} />
                    <Route path="/simulator" element={<CollegeSimulator />} />
                    <Route path="/study-plan" element={<StudyPlan />} />
                    <Route path="/profile" element={<Profile />} />
                    <Route
                      path="/admin"
                      element={
                        <AdminRoute>
                          <Admin />
                        </AdminRoute>
                      }
                    />
                  </Route>

                  {/* 404 Catch-all */}
                  <Route path="*" element={<NotFound />} />
                </Routes>
              </Suspense>
            </RouteErrorBoundary>
          </BrowserRouter>
        </AuthProvider>
      </ThemeProvider>
    </QueryClientProvider>
  );
};

export default App;
