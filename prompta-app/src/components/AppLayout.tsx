
import { useState } from "react";
import { Outlet, NavLink, useLocation, useNavigate } from "react-router-dom";
import { Search, Plus, FileText, Folder, Key, User, Settings, LayoutDashboard, LogOut, Puzzle, Building, Book, Zap } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { 
  DropdownMenu, 
  DropdownMenuContent, 
  DropdownMenuItem, 
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger 
} from "@/components/ui/dropdown-menu";
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarProvider,
  SidebarTrigger,
  useSidebar,
} from "@/components/ui/sidebar";
import { useAuth } from "@/components/auth/AuthProvider";
import { useProfile } from "@/hooks/useProfile";
import { useIsMobile } from "@/hooks/use-mobile";

const navigation = [
  { name: "Dashboard", href: "/", icon: LayoutDashboard },
  { name: "Projects", href: "/projects", icon: Folder },
  { name: "Prompts", href: "/prompts", icon: FileText },
  { name: "Playground", href: "/playground", icon: Zap },
  { name: "Organizations", href: "/organizations", icon: Building },
  { name: "API Keys", href: "/api-keys", icon: Key },
  { name: "Extensions", href: "/extensions", icon: Puzzle },
  { name: "Documentation", href: "/documentation", icon: Book },
];

const AppSidebar = () => {
  const location = useLocation();
  const { state } = useSidebar();
  const { signOut } = useAuth();
  const { data: profile } = useProfile();

  const isActive = (path: string) => {
    if (path === "/") {
      return location.pathname === "/";
    }
    return location.pathname.startsWith(path);
  };

  const handleSignOut = () => {
    signOut();
  };

  const userInitials = profile 
    ? `${profile.first_name?.[0] || ''}${profile.last_name?.[0] || ''}`.toUpperCase() || profile.email[0].toUpperCase()
    : 'U';

  const userName = profile 
    ? `${profile.first_name || ''} ${profile.last_name || ''}`.trim() || profile.email
    : 'User';

  return (
    <Sidebar>
      <SidebarHeader className="border-b">
        <div className="flex items-center space-x-2 p-2">
          <div className="h-8 w-8 rounded-lg bg-primary flex items-center justify-center">
            <FileText className="h-4 w-4 text-primary-foreground" />
          </div>
          {state !== "collapsed" && (
            <span className="text-xl font-semibold">Prompta</span>
          )}
        </div>
      </SidebarHeader>

      <SidebarContent>
        <SidebarGroup>
          <SidebarGroupLabel>Main Navigation</SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu>
              {navigation.map((item) => (
                <SidebarMenuItem key={item.name}>
                  <SidebarMenuButton asChild isActive={isActive(item.href)}>
                    <NavLink to={item.href}>
                      <item.icon className="h-4 w-4" />
                      <span>{item.name}</span>
                    </NavLink>
                  </SidebarMenuButton>
                </SidebarMenuItem>
              ))}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>

      <SidebarFooter className="border-t">
        <SidebarMenu>
          <SidebarMenuItem>
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <SidebarMenuButton className="w-full">
                  <Avatar className="h-6 w-6">
                    <AvatarFallback className="text-xs">{userInitials}</AvatarFallback>
                  </Avatar>
                  {state !== "collapsed" && (
                    <div className="flex flex-col text-left">
                      <span className="text-sm font-medium">{userName}</span>
                      <span className="text-xs text-muted-foreground">{profile?.email}</span>
                    </div>
                  )}
                </SidebarMenuButton>
              </DropdownMenuTrigger>
              <DropdownMenuContent className="w-56" align="end" side="right">
                <DropdownMenuLabel className="font-normal">
                  <div className="flex flex-col space-y-1">
                    <p className="text-sm font-medium leading-none">{userName}</p>
                    <p className="text-xs leading-none text-muted-foreground">
                      {profile?.email}
                    </p>
                  </div>
                </DropdownMenuLabel>
                <DropdownMenuSeparator />
                <DropdownMenuItem asChild>
                  <NavLink to="/profile" className="flex items-center w-full">
                    <User className="mr-2 h-4 w-4" />
                    <span>Profile</span>
                  </NavLink>
                </DropdownMenuItem>
                <DropdownMenuItem>
                  <Settings className="mr-2 h-4 w-4" />
                  <span>Settings</span>
                </DropdownMenuItem>
                <DropdownMenuSeparator />
                <DropdownMenuItem onClick={handleSignOut}>
                  <LogOut className="mr-2 h-4 w-4" />
                  <span>Log out</span>
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </SidebarMenuItem>
        </SidebarMenu>
      </SidebarFooter>
    </Sidebar>
  );
};

const AppLayout = () => {
  const [searchQuery, setSearchQuery] = useState("");
  const isMobile = useIsMobile();
  const location = useLocation();
  const navigate = useNavigate();

  const getCreateOptions = () => {
    const currentPath = location.pathname;
    
    // Context-aware creation options based on current route
    if (currentPath === "/prompts") {
      return [
        { label: "New Prompt", action: () => console.log("Create prompt"), icon: FileText },
      ];
    }
    
    if (currentPath === "/organizations") {
      return [
        { label: "New Organization", action: () => navigate("/organizations"), icon: Building },
      ];
    }
    
    if (currentPath === "/api-keys") {
      return [
        { label: "New API Key", action: () => navigate("/api-keys"), icon: Key },
      ];
    }
    
    if (currentPath === "/projects") {
      return [
        { label: "New Project", action: () => console.log("Create project"), icon: Folder },
      ];
    }
    
    // Default options for dashboard and other pages
    return [
      { label: "New Prompt", action: () => navigate("/prompts"), icon: FileText },
      { label: "New Project", action: () => navigate("/projects"), icon: Folder },
      { label: "New Organization", action: () => navigate("/organizations"), icon: Building },
      { label: "Generate API Key", action: () => navigate("/api-keys"), icon: Key },
    ];
  };

  const createOptions = getCreateOptions();

  return (
    <SidebarProvider>
      <div className="min-h-screen flex w-full">
        <AppSidebar />
        
        <div className="flex-1 flex flex-col">
          {/* Header */}
          <header className="border-b bg-card/95 backdrop-blur supports-[backdrop-filter]:bg-card/60 sticky top-0 z-50">
            <div className="flex items-center justify-between px-4 sm:px-6 py-3 sm:py-4">
              <div className="flex items-center space-x-4">
                <SidebarTrigger />
              </div>
              <div className="flex items-center space-x-2 sm:space-x-4">
                <div className={`relative ${isMobile ? 'w-40' : 'w-64'}`}>
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                  <Input
                    placeholder="Search prompts..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="pl-10 text-sm"
                  />
                </div>
                
                {createOptions.length === 1 ? (
                  <Button size={isMobile ? "sm" : "default"} onClick={createOptions[0].action}>
                    <Plus className="h-4 w-4 mr-2" />
                    {!isMobile && "Create"}
                  </Button>
                ) : (
                  <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                      <Button size={isMobile ? "sm" : "default"}>
                        <Plus className="h-4 w-4 mr-2" />
                        {!isMobile && "Create"}
                      </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end" className="w-48">
                      <DropdownMenuLabel>Create New</DropdownMenuLabel>
                      <DropdownMenuSeparator />
                      {createOptions.map((option, index) => (
                        <DropdownMenuItem key={index} onClick={option.action}>
                          <option.icon className="mr-2 h-4 w-4" />
                          <span>{option.label}</span>
                        </DropdownMenuItem>
                      ))}
                    </DropdownMenuContent>
                  </DropdownMenu>
                )}
              </div>
            </div>
          </header>

          {/* Main Content */}
          <main className="flex-1 overflow-auto">
            <div className="container mx-auto px-4 sm:px-6 py-4 sm:py-8">
              <Outlet />
            </div>
          </main>
        </div>
      </div>
    </SidebarProvider>
  );
};

export default AppLayout;
