
import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { AuthProvider, useAuth } from "@/components/auth/AuthProvider";
import { AuthPage } from "@/components/auth/AuthPage";
import Index from "./pages/Index";
import ProjectsPage from "./components/ProjectsPage";
import PromptsPage from "./components/PromptsPage";
import ApiKeysPage from "./components/ApiKeysPage";
import UserProfilePage from "./components/UserProfilePage";
import OrganizationsPage from "./components/OrganizationsPage";
import DocumentationPage from "./components/DocumentationPage";
import PlaygroundPage from "./components/PlaygroundPage";
import NotFound from "./pages/NotFound";
import AppLayout from "./components/AppLayout";
import ExtensionsPage from "./components/ExtensionsPage";

const queryClient = new QueryClient();

const AppRoutes = () => {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent mx-auto mb-4"></div>
          <p className="text-muted-foreground">Loading...</p>
        </div>
      </div>
    );
  }

  if (!user) {
    return <AuthPage />;
  }

  return (
    <Routes>
      <Route path="/" element={<AppLayout />}>
        <Route index element={<Index />} />
        <Route path="projects" element={<ProjectsPage />} />
        <Route path="prompts" element={<PromptsPage />} />
        <Route path="playground" element={<PlaygroundPage />} />
        <Route path="api-keys" element={<ApiKeysPage />} />
        <Route path="extensions" element={<ExtensionsPage />} />
        <Route path="organizations" element={<OrganizationsPage />} />
        <Route path="documentation" element={<DocumentationPage />} />
        <Route path="profile" element={<UserProfilePage />} />
      </Route>
      <Route path="*" element={<NotFound />} />
    </Routes>
  );
};

const App = () => (
  <QueryClientProvider client={queryClient}>
    <TooltipProvider>
      <Toaster />
      <Sonner />
      <BrowserRouter>
        <AuthProvider>
          <AppRoutes />
        </AuthProvider>
      </BrowserRouter>
    </TooltipProvider>
  </QueryClientProvider>
);

export default App;
