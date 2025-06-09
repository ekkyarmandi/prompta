
import { useState } from "react";
import { Book, FileText, Folder, Building, Key, Puzzle, Search, Plus, Download, Bookmark, Users, Settings } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";

const DocumentationPage = () => {
  const [activeSection, setActiveSection] = useState("getting-started");

  const sections = [
    { id: "getting-started", title: "Getting Started", icon: Book },
    { id: "prompts", title: "Prompts", icon: FileText },
    { id: "projects", title: "Projects", icon: Folder },
    { id: "organizations", title: "Organizations", icon: Building },
    { id: "api-keys", title: "API Keys", icon: Key },
    { id: "extensions", title: "Extensions", icon: Puzzle },
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Documentation</h1>
          <p className="text-muted-foreground">
            Learn how to use Prompta effectively
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Navigation Sidebar */}
        <div className="lg:col-span-1">
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Contents</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              {sections.map((section) => (
                <button
                  key={section.id}
                  onClick={() => setActiveSection(section.id)}
                  className={`w-full flex items-center space-x-2 px-3 py-2 text-left rounded-md transition-colors ${
                    activeSection === section.id
                      ? "bg-primary text-primary-foreground"
                      : "hover:bg-muted"
                  }`}
                >
                  <section.icon className="h-4 w-4" />
                  <span>{section.title}</span>
                </button>
              ))}
            </CardContent>
          </Card>
        </div>

        {/* Content Area */}
        <div className="lg:col-span-3">
          <Card>
            <CardContent className="p-6">
              {activeSection === "getting-started" && (
                <div className="space-y-6">
                  <div>
                    <h2 className="text-2xl font-bold mb-4">Getting Started with Prompta</h2>
                    <p className="text-muted-foreground mb-4">
                      Welcome to Prompta! This guide will help you understand and use all the features available in the application.
                    </p>
                  </div>

                  <div className="space-y-4">
                    <h3 className="text-xl font-semibold">What is Prompta?</h3>
                    <p className="text-muted-foreground">
                      Prompta is a comprehensive prompt management platform that helps you organize, share, and collaborate on AI prompts and projects.
                    </p>
                  </div>

                  <div className="space-y-4">
                    <h3 className="text-xl font-semibold">Main Features</h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      {sections.slice(1).map((feature) => (
                        <div key={feature.id} className="flex items-start space-x-3 p-3 border rounded-lg">
                          <feature.icon className="h-5 w-5 text-primary mt-0.5" />
                          <div>
                            <h4 className="font-medium">{feature.title}</h4>
                            <p className="text-sm text-muted-foreground">
                              {feature.id === "prompts" && "Create, organize and share AI prompts"}
                              {feature.id === "projects" && "Manage your AI projects and workflows"}
                              {feature.id === "organizations" && "Collaborate with team members"}
                              {feature.id === "api-keys" && "Manage external service integrations"}
                              {feature.id === "extensions" && "Extend functionality with plugins"}
                            </p>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              )}

              {activeSection === "prompts" && (
                <div className="space-y-6">
                  <div>
                    <h2 className="text-2xl font-bold mb-4">Managing Prompts</h2>
                    <p className="text-muted-foreground mb-4">
                      Learn how to create, organize, and share your AI prompts effectively.
                    </p>
                  </div>

                  <div className="space-y-6">
                    <div>
                      <h3 className="text-xl font-semibold mb-3">Creating Prompts</h3>
                      <div className="space-y-3">
                        <p className="text-muted-foreground">To create a new prompt:</p>
                        <ol className="list-decimal list-inside space-y-2 text-muted-foreground ml-4">
                          <li>Click the <Badge variant="outline"><Plus className="h-3 w-3 mr-1" />Create</Badge> button in the header</li>
                          <li>Fill in the prompt title and description</li>
                          <li>Add your prompt content and any necessary parameters</li>
                          <li>Set visibility and organization settings</li>
                          <li>Save your prompt</li>
                        </ol>
                      </div>
                    </div>

                    <Separator />

                    <div>
                      <h3 className="text-xl font-semibold mb-3">Using Prompts</h3>
                      <div className="space-y-3">
                        <p className="text-muted-foreground">To use and manage your prompts:</p>
                        <ul className="list-disc list-inside space-y-2 text-muted-foreground ml-4">
                          <li><Badge variant="outline"><Bookmark className="h-3 w-3 mr-1" />Bookmark</Badge> prompts to save them to your collection</li>
                          <li>Click <Badge variant="outline">Copy</Badge> to copy the prompt content</li>
                          <li>Use the search bar to find specific prompts quickly</li>
                          <li>Filter prompts by category, author, or organization</li>
                        </ul>
                      </div>
                    </div>

                    <Separator />

                    <div>
                      <h3 className="text-xl font-semibold mb-3">Prompt Versions</h3>
                      <p className="text-muted-foreground">
                        Each prompt can have multiple versions, allowing you to iterate and improve while maintaining history. 
                        The active version is the one that will be used by default.
                      </p>
                    </div>
                  </div>
                </div>
              )}

              {activeSection === "projects" && (
                <div className="space-y-6">
                  <div>
                    <h2 className="text-2xl font-bold mb-4">Project Management</h2>
                    <p className="text-muted-foreground mb-4">
                      Organize your AI workflows and collaborate on projects with your team.
                    </p>
                  </div>

                  <div className="space-y-6">
                    <div>
                      <h3 className="text-xl font-semibold mb-3">Creating Projects</h3>
                      <p className="text-muted-foreground">
                        Projects help you group related prompts and organize your AI workflows. You can create personal projects 
                        or team projects within your organization.
                      </p>
                    </div>

                    <Separator />

                    <div>
                      <h3 className="text-xl font-semibold mb-3">Project Features</h3>
                      <ul className="list-disc list-inside space-y-2 text-muted-foreground ml-4">
                        <li>Group related prompts together</li>
                        <li>Set project visibility (private, team, or public)</li>
                        <li>Collaborate with team members</li>
                        <li>Track project progress and versions</li>
                        <li>Export project data</li>
                      </ul>
                    </div>
                  </div>
                </div>
              )}

              {activeSection === "organizations" && (
                <div className="space-y-6">
                  <div>
                    <h2 className="text-2xl font-bold mb-4">Organizations & Teams</h2>
                    <p className="text-muted-foreground mb-4">
                      Collaborate with your team members and manage organizational settings.
                    </p>
                  </div>

                  <div className="space-y-6">
                    <div>
                      <h3 className="text-xl font-semibold mb-3">Organization Roles</h3>
                      <div className="space-y-3">
                        <div className="flex items-center space-x-2">
                          <Badge variant="default">Owner</Badge>
                          <span className="text-muted-foreground">Full access to all organization settings and content</span>
                        </div>
                        <div className="flex items-center space-x-2">
                          <Badge variant="secondary">Admin</Badge>
                          <span className="text-muted-foreground">Can manage members and most organization settings</span>
                        </div>
                        <div className="flex items-center space-x-2">
                          <Badge variant="outline">Member</Badge>
                          <span className="text-muted-foreground">Can access and contribute to organization content</span>
                        </div>
                      </div>
                    </div>

                    <Separator />

                    <div>
                      <h3 className="text-xl font-semibold mb-3">Managing Organizations</h3>
                      <ul className="list-disc list-inside space-y-2 text-muted-foreground ml-4">
                        <li>Create new organizations for your teams</li>
                        <li>Invite team members via email</li>
                        <li>Set organization visibility and permissions</li>
                        <li>Manage shared prompts and projects</li>
                        <li>Configure organization settings</li>
                      </ul>
                    </div>
                  </div>
                </div>
              )}

              {activeSection === "api-keys" && (
                <div className="space-y-6">
                  <div>
                    <h2 className="text-2xl font-bold mb-4">API Key Management</h2>
                    <p className="text-muted-foreground mb-4">
                      Manage your external service integrations and API keys securely.
                    </p>
                  </div>

                  <div className="space-y-6">
                    <div>
                      <h3 className="text-xl font-semibold mb-3">Supported Services</h3>
                      <p className="text-muted-foreground mb-3">
                        Connect to various AI services and platforms:
                      </p>
                      <ul className="list-disc list-inside space-y-2 text-muted-foreground ml-4">
                        <li>OpenAI (GPT models)</li>
                        <li>Anthropic (Claude models)</li>
                        <li>Google (Gemini models)</li>
                        <li>Custom API endpoints</li>
                      </ul>
                    </div>

                    <Separator />

                    <div>
                      <h3 className="text-xl font-semibold mb-3">Security</h3>
                      <p className="text-muted-foreground">
                        All API keys are encrypted and stored securely. Keys are only accessible to you and are never 
                        shared with other users or organizations unless explicitly configured.
                      </p>
                    </div>
                  </div>
                </div>
              )}

              {activeSection === "extensions" && (
                <div className="space-y-6">
                  <div>
                    <h2 className="text-2xl font-bold mb-4">Extensions</h2>
                    <p className="text-muted-foreground mb-4">
                      Extend Prompta's functionality with custom extensions and integrations.
                    </p>
                  </div>

                  <div className="space-y-6">
                    <div>
                      <h3 className="text-xl font-semibold mb-3">Available Extensions</h3>
                      <p className="text-muted-foreground">
                        Browse and install extensions to add new features:
                      </p>
                      <ul className="list-disc list-inside space-y-2 text-muted-foreground ml-4">
                        <li>Custom prompt templates</li>
                        <li>External tool integrations</li>
                        <li>Workflow automation</li>
                        <li>Export/import utilities</li>
                        <li>Custom UI components</li>
                      </ul>
                    </div>

                    <Separator />

                    <div>
                      <h3 className="text-xl font-semibold mb-3">Installing Extensions</h3>
                      <ol className="list-decimal list-inside space-y-2 text-muted-foreground ml-4">
                        <li>Browse the extension marketplace</li>
                        <li>Click "Install" on the extension you want</li>
                        <li>Configure any required settings</li>
                        <li>The extension will be available in your workspace</li>
                      </ol>
                    </div>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default DocumentationPage;
