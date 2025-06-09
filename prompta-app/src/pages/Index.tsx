
import { useState } from "react";
import { Search, Plus, Key, User, Folder, FileText, Settings } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Separator } from "@/components/ui/separator";
import { useProfile } from "@/hooks/useProfile";
import { useOrganizations } from "@/hooks/useOrganizations";

const Dashboard = () => {
  const { data: profile } = useProfile();
  const { data: organizations } = useOrganizations();

  // Mock data for demonstration - replace with real data queries later
  const stats = {
    totalProjects: 0,
    totalPrompts: 0,
    activeApiKeys: 0,
    recentActivity: 0
  };

  const recentProjects: any[] = [];
  const recentPrompts: any[] = [];

  const userName = profile 
    ? `${profile.first_name || ''} ${profile.last_name || ''}`.trim() || profile.email
    : 'User';

  return (
    <div>
      {/* Welcome Section */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2">Welcome back, {profile?.first_name || 'there'}</h1>
        <p className="text-muted-foreground">Manage your AI prompts and projects efficiently</p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Organizations</CardTitle>
            <Folder className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{organizations?.length || 0}</div>
            <p className="text-xs text-muted-foreground">Organizations you belong to</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Prompts</CardTitle>
            <FileText className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.totalPrompts}</div>
            <p className="text-xs text-muted-foreground">Ready to be used</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Active API Keys</CardTitle>
            <Key className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.activeApiKeys}</div>
            <p className="text-xs text-muted-foreground">For API access</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Recent Activity</CardTitle>
            <User className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.recentActivity}</div>
            <p className="text-xs text-muted-foreground">Actions this week</p>
          </CardContent>
        </Card>
      </div>

      {/* Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Organizations */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center justify-between">
              Your Organizations
              <Button variant="outline" size="sm">
                View All
              </Button>
            </CardTitle>
            <CardDescription>Organizations you're a member of</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {organizations && organizations.length > 0 ? (
                organizations.map((org: any) => (
                  <div key={org.id} className="flex items-center justify-between p-4 border rounded-lg hover:bg-muted/50 transition-colors cursor-pointer">
                    <div className="flex-1">
                      <h4 className="font-semibold">{org.name}</h4>
                      <p className="text-sm text-muted-foreground">{org.description || 'No description'}</p>
                      <div className="flex items-center space-x-4 mt-2">
                        <Badge variant="secondary" className="text-xs">
                          {org.organization_memberships[0]?.role}
                        </Badge>
                        <span className="text-xs text-muted-foreground">
                          Created {new Date(org.created_at).toLocaleDateString()}
                        </span>
                      </div>
                    </div>
                    <div className="h-8 w-8 rounded-lg bg-primary/10 flex items-center justify-center">
                      <Folder className="h-4 w-4 text-primary" />
                    </div>
                  </div>
                ))
              ) : (
                <div className="text-center p-8 text-muted-foreground">
                  <Folder className="h-12 w-12 mx-auto mb-4 opacity-50" />
                  <p>No organizations yet</p>
                  <p className="text-sm">Create or join an organization to get started</p>
                </div>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Recent Prompts */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center justify-between">
              Recent Prompts
              <Button variant="outline" size="sm">
                View All
              </Button>
            </CardTitle>
            <CardDescription>Your latest prompt versions</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {recentPrompts.length > 0 ? (
                recentPrompts.map((prompt: any) => (
                  <div key={prompt.id} className="flex items-center justify-between p-4 border rounded-lg hover:bg-muted/50 transition-colors cursor-pointer">
                    <div className="flex-1">
                      <div className="flex items-center space-x-2">
                        <h4 className="font-semibold">{prompt.name}</h4>
                        <Badge variant="secondary" className="text-xs">{prompt.version}</Badge>
                      </div>
                      <p className="text-sm text-muted-foreground">{prompt.project}</p>
                      <div className="flex items-center space-x-2 mt-2">
                        {prompt.tags?.map((tag: string) => (
                          <Badge key={tag} variant="outline" className="text-xs">{tag}</Badge>
                        ))}
                      </div>
                    </div>
                    <div className="h-8 w-8 rounded-lg bg-secondary/50 flex items-center justify-center">
                      <FileText className="h-4 w-4 text-secondary-foreground" />
                    </div>
                  </div>
                ))
              ) : (
                <div className="text-center p-8 text-muted-foreground">
                  <FileText className="h-12 w-12 mx-auto mb-4 opacity-50" />
                  <p>No prompts yet</p>
                  <p className="text-sm">Create your first prompt to get started</p>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Quick Actions */}
      <Card className="mt-8">
        <CardHeader>
          <CardTitle>Quick Actions</CardTitle>
          <CardDescription>Get started with common tasks</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Button variant="outline" className="h-auto p-6 flex flex-col items-center space-y-2">
              <Plus className="h-8 w-8 text-primary" />
              <span className="font-semibold">Create Organization</span>
              <span className="text-sm text-muted-foreground text-center">Start organizing your team</span>
            </Button>
            <Button variant="outline" className="h-auto p-6 flex flex-col items-center space-y-2">
              <FileText className="h-8 w-8 text-primary" />
              <span className="font-semibold">Add New Prompt</span>
              <span className="text-sm text-muted-foreground text-center">Create your next AI prompt</span>
            </Button>
            <Button variant="outline" className="h-auto p-6 flex flex-col items-center space-y-2">
              <Key className="h-8 w-8 text-primary" />
              <span className="font-semibold">Generate API Key</span>
              <span className="text-sm text-muted-foreground text-center">Access your prompts programmatically</span>
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default Dashboard;
