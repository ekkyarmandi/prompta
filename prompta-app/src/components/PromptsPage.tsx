import { useState } from "react";
import { Search, Plus, Filter, MoreHorizontal, FileText, Tag, Eye, Edit, Copy, Hash, Play } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from "@/components/ui/dropdown-menu";
import { Switch } from "@/components/ui/switch";
import { usePromptDownloads, usePromptDownloadCounts } from "@/hooks/usePromptDownloads";
import { estimateTokenCount, formatTokenCount } from "@/utils/tokenCounter";

const PromptsPage = () => {
  const [searchQuery, setSearchQuery] = useState("");
  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false);
  const [selectedProject, setSelectedProject] = useState("all");
  const [newPrompt, setNewPrompt] = useState({
    name: "",
    description: "",
    content: "",
    location: "",
    tags: "",
    projectId: "",
    isPublic: false,
    notes: ""
  });

  const { downloadPrompt, isDownloading } = usePromptDownloads();
  const { data: downloadCounts = [] } = usePromptDownloadCounts();

  // Mock data
  const projects = [
    { id: "1", name: "E-commerce Assistant" },
    { id: "2", name: "Content Generation" },
    { id: "3", name: "Data Analysis" },
    { id: "4", name: "Code Review Assistant" }
  ];

  const prompts = [
    {
      id: 1,
      name: "Product Description Generator",
      description: "Generate compelling product descriptions for e-commerce",
      content: "You are an expert copywriter. Create a compelling product description for: {{ product_name }}...",
      location: "/ecommerce/product-description",
      tags: ["product", "content", "ecommerce"],
      project: "E-commerce Assistant",
      version: "v2.1",
      isPublic: false,
      lastUpdated: "2 hours ago",
      createdAt: "2024-01-15"
    },
    {
      id: 2,
      name: "Customer Support Response",
      description: "Professional customer support email responses",
      content: "You are a helpful customer service representative. Respond to this customer inquiry: {{ inquiry }}...",
      location: "/ecommerce/support-response",
      tags: ["support", "response", "customer"],
      project: "E-commerce Assistant",
      version: "v1.5",
      isPublic: true,
      lastUpdated: "1 day ago",
      createdAt: "2024-01-12"
    },
    {
      id: 3,
      name: "Blog Outline Creator",
      description: "Create detailed blog post outlines",
      content: "Create a comprehensive blog post outline for the topic: {{ topic }}...",
      location: "/content/blog-outline",
      tags: ["blog", "outline", "content"],
      project: "Content Generation",
      version: "v3.0",
      isPublic: true,
      lastUpdated: "3 days ago",
      createdAt: "2024-01-10"
    },
    {
      id: 4,
      name: "SQL Query Helper",
      description: "Generate and optimize SQL queries",
      content: "You are a database expert. Write an efficient SQL query for: {{ requirement }}...",
      location: "/analytics/sql-helper",
      tags: ["sql", "query", "database"],
      project: "Data Analysis",
      version: "v1.2",
      isPublic: false,
      lastUpdated: "1 week ago",
      createdAt: "2024-01-05"
    },
    {
      id: 5,
      name: "Code Review Checklist",
      description: "Comprehensive code review guidelines",
      content: "Review the following code and provide feedback on: {{ code }}...",
      location: "/code-review/checklist",
      tags: ["code", "review", "quality"],
      project: "Code Review Assistant",
      version: "v2.0",
      isPublic: true,
      lastUpdated: "2 weeks ago",
      createdAt: "2023-12-28"
    },
    {
      id: 6,
      name: "Social Media Post Generator",
      description: "Create engaging social media content",
      content: "Create an engaging social media post about: {{ topic }}...",
      location: "/content/social-media",
      tags: ["social", "content", "marketing"],
      project: "Content Generation",
      version: "v1.8",
      isPublic: false,
      lastUpdated: "3 weeks ago",
      createdAt: "2023-12-20"
    }
  ];

  const filteredPrompts = prompts.filter(prompt => {
    const matchesSearch = prompt.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         prompt.description.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         prompt.tags.some(tag => tag.toLowerCase().includes(searchQuery.toLowerCase()));
    
    const matchesProject = selectedProject === "all" || prompt.project === projects.find(p => p.id === selectedProject)?.name;
    
    return matchesSearch && matchesProject;
  });

  const handleTestInPlayground = (prompt: any) => {
    // Store the prompt content in localStorage for the playground
    localStorage.setItem("playground-prompt", JSON.stringify({
      name: prompt.name,
      content: prompt.content
    }));
    
    // Navigate to playground
    window.location.href = "/playground";
  };

  const handleCreatePrompt = () => {
    console.log("Creating prompt:", newPrompt);
    setIsCreateDialogOpen(false);
    setNewPrompt({
      name: "",
      description: "",
      content: "",
      location: "",
      tags: "",
      projectId: "",
      isPublic: false,
      notes: ""
    });
  };

  const handleCopyPrompt = (promptId: number) => {
    downloadPrompt(promptId.toString());
  };

  const getCopyCount = (promptId: number) => {
    const count = downloadCounts.find(dc => dc.prompt_id === promptId.toString());
    return count?.download_count || 0;
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Prompts Library</h1>
          <p className="text-muted-foreground">Browse and manage your AI prompts</p>
        </div>
        <Dialog open={isCreateDialogOpen} onOpenChange={setIsCreateDialogOpen}>
          <DialogTrigger asChild>
            <Button>
              <Plus className="h-4 w-4 mr-2" />
              New Prompt
            </Button>
          </DialogTrigger>
          <DialogContent className="max-w-2xl">
            <DialogHeader>
              <DialogTitle>Create New Prompt</DialogTitle>
              <DialogDescription>
                Add a new prompt to your library
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-4 max-h-96 overflow-y-auto">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="prompt-name">Prompt Name</Label>
                  <Input
                    id="prompt-name"
                    value={newPrompt.name}
                    onChange={(e) => setNewPrompt({ ...newPrompt, name: e.target.value })}
                    placeholder="My Awesome Prompt"
                  />
                </div>
                <div>
                  <Label htmlFor="project">Project</Label>
                  <Select value={newPrompt.projectId} onValueChange={(value) => setNewPrompt({ ...newPrompt, projectId: value })}>
                    <SelectTrigger>
                      <SelectValue placeholder="Select project" />
                    </SelectTrigger>
                    <SelectContent>
                      {projects.map((project) => (
                        <SelectItem key={project.id} value={project.id}>
                          {project.name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>
              <div>
                <Label htmlFor="description">Description</Label>
                <Textarea
                  id="description"
                  value={newPrompt.description}
                  onChange={(e) => setNewPrompt({ ...newPrompt, description: e.target.value })}
                  placeholder="What does this prompt do?"
                />
              </div>
              <div>
                <div className="flex items-center justify-between mb-2">
                  <Label htmlFor="content">Prompt Content</Label>
                  <Badge variant="outline" className="flex items-center space-x-1">
                    <Hash className="h-3 w-3" />
                    <span>{formatTokenCount(estimateTokenCount(newPrompt.content))} tokens</span>
                  </Badge>
                </div>
                <Textarea
                  id="content"
                  value={newPrompt.content}
                  onChange={(e) => setNewPrompt({ ...newPrompt, content: e.target.value })}
                  placeholder="You are a helpful assistant..."
                  className="min-h-24"
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="location">Location Path</Label>
                  <Input
                    id="location"
                    value={newPrompt.location}
                    onChange={(e) => setNewPrompt({ ...newPrompt, location: e.target.value })}
                    placeholder="/category/prompt-name"
                  />
                </div>
                <div>
                  <Label htmlFor="tags">Tags (comma-separated)</Label>
                  <Input
                    id="tags"
                    value={newPrompt.tags}
                    onChange={(e) => setNewPrompt({ ...newPrompt, tags: e.target.value })}
                    placeholder="tag1, tag2, tag3"
                  />
                </div>
              </div>
              <div className="flex items-center space-x-2">
                <Switch
                  id="public"
                  checked={newPrompt.isPublic}
                  onCheckedChange={(checked) => setNewPrompt({ ...newPrompt, isPublic: checked })}
                />
                <Label htmlFor="public">Make this prompt public</Label>
              </div>
              <div>
                <Label htmlFor="notes">Notes</Label>
                <Textarea
                  id="notes"
                  value={newPrompt.notes}
                  onChange={(e) => setNewPrompt({ ...newPrompt, notes: e.target.value })}
                  placeholder="Additional notes about this prompt..."
                />
              </div>
            </div>
            <div className="flex justify-end space-x-2">
              <Button variant="outline" onClick={() => setIsCreateDialogOpen(false)}>
                Cancel
              </Button>
              <Button onClick={handleCreatePrompt}>
                Create Prompt
              </Button>
            </div>
          </DialogContent>
        </Dialog>
      </div>

      {/* Search and Filters */}
      <div className="flex items-center space-x-4">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search prompts..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-10"
          />
        </div>
        <Select value={selectedProject} onValueChange={setSelectedProject}>
          <SelectTrigger className="w-48">
            <SelectValue placeholder="Filter by project" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Projects</SelectItem>
            {projects.map((project) => (
              <SelectItem key={project.id} value={project.id}>
                {project.name}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        <Button variant="outline">
          <Filter className="h-4 w-4 mr-2" />
          More Filters
        </Button>
      </div>

      {/* Prompts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {filteredPrompts.map((prompt) => {
          const tokenCount = estimateTokenCount(prompt.content);
          
          return (
            <Card key={prompt.id} className="hover:shadow-md transition-shadow group">
              <CardHeader>
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center space-x-2 mb-2">
                      <CardTitle className="group-hover:text-primary transition-colors">
                        {prompt.name}
                      </CardTitle>
                      <Badge variant="secondary">{prompt.version}</Badge>
                      {prompt.isPublic && (
                        <Badge variant="outline">Public</Badge>
                      )}
                      <Badge variant="outline" className="flex items-center space-x-1">
                        <Hash className="h-3 w-3" />
                        <span>{formatTokenCount(tokenCount)} tokens</span>
                      </Badge>
                    </div>
                    <CardDescription>{prompt.description}</CardDescription>
                    <p className="text-sm text-muted-foreground mt-2">{prompt.project}</p>
                  </div>
                  <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                      <Button variant="ghost" size="sm">
                        <MoreHorizontal className="h-4 w-4" />
                      </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end">
                      <DropdownMenuItem onClick={() => handleTestInPlayground(prompt)}>
                        <Play className="h-4 w-4 mr-2" />
                        Test in Playground
                      </DropdownMenuItem>
                      <DropdownMenuItem>
                        <Eye className="h-4 w-4 mr-2" />
                        View Details
                      </DropdownMenuItem>
                      <DropdownMenuItem>
                        <Edit className="h-4 w-4 mr-2" />
                        Edit Prompt
                      </DropdownMenuItem>
                      {prompt.isPublic && (
                        <DropdownMenuItem onClick={() => handleCopyPrompt(prompt.id)}>
                          <Copy className="h-4 w-4 mr-2" />
                          Copy
                        </DropdownMenuItem>
                      )}
                      <DropdownMenuItem>Create Version</DropdownMenuItem>
                      <DropdownMenuItem>Copy to Project</DropdownMenuItem>
                      <DropdownMenuItem className="text-destructive">Delete</DropdownMenuItem>
                    </DropdownMenuContent>
                  </DropdownMenu>
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="bg-muted/50 p-3 rounded-lg">
                    <p className="text-sm font-mono line-clamp-3">{prompt.content}</p>
                  </div>
                  
                  <div className="flex items-center space-x-2">
                    <Tag className="h-3 w-3 text-muted-foreground" />
                    <div className="flex flex-wrap gap-1">
                      {prompt.tags.map((tag) => (
                        <Badge key={tag} variant="outline" className="text-xs">
                          {tag}
                        </Badge>
                      ))}
                    </div>
                  </div>

                  <div className="flex items-center justify-between text-xs text-muted-foreground pt-2 border-t">
                    <div className="flex items-center space-x-4">
                      <span>Location: <code className="bg-muted px-1 py-0.5 rounded">{prompt.location}</code></span>
                      {prompt.isPublic && (
                        <span className="flex items-center space-x-1">
                          <Copy className="h-3 w-3" />
                          <span>{getCopyCount(prompt.id)} copies</span>
                        </span>
                      )}
                    </div>
                    <span>Updated {prompt.lastUpdated}</span>
                  </div>
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>

      {filteredPrompts.length === 0 && (
        <div className="text-center py-12">
          <FileText className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
          <h3 className="text-lg font-semibold mb-2">No prompts found</h3>
          <p className="text-muted-foreground mb-4">
            {searchQuery ? "Try adjusting your search terms" : "Create your first prompt to get started"}
          </p>
          {!searchQuery && (
            <Button onClick={() => setIsCreateDialogOpen(true)}>
              <Plus className="h-4 w-4 mr-2" />
              Create Prompt
            </Button>
          )}
        </div>
      )}
    </div>
  );
};

export default PromptsPage;
