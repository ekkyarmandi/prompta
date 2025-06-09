
import { useState } from "react";
import { Search, Plus, Filter, MoreHorizontal, Folder, Calendar, FileText } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from "@/components/ui/dropdown-menu";

const ProjectsPage = () => {
  const [searchQuery, setSearchQuery] = useState("");
  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false);
  const [newProject, setNewProject] = useState({
    name: "",
    description: "",
    directory: ""
  });

  // Mock data
  const projects = [
    {
      id: 1,
      name: "E-commerce Assistant",
      description: "Customer support and product recommendation prompts for online retail",
      directory: "/ecommerce",
      promptCount: 24,
      lastUpdated: "2 hours ago",
      createdAt: "2024-01-15",
      isPublic: false
    },
    {
      id: 2,
      name: "Content Generation",
      description: "Blog posts, social media, and marketing content creation prompts",
      directory: "/content",
      promptCount: 18,
      lastUpdated: "1 day ago",
      createdAt: "2024-01-10",
      isPublic: true
    },
    {
      id: 3,
      name: "Data Analysis",
      description: "SQL queries, data visualization, and statistical analysis prompts",
      directory: "/analytics",
      promptCount: 32,
      lastUpdated: "3 days ago",
      createdAt: "2024-01-05",
      isPublic: false
    },
    {
      id: 4,
      name: "Code Review Assistant",
      description: "Code review, debugging, and optimization prompts for development teams",
      directory: "/code-review",
      promptCount: 15,
      lastUpdated: "1 week ago",
      createdAt: "2023-12-28",
      isPublic: true
    },
    {
      id: 5,
      name: "Legal Document Helper",
      description: "Contract analysis, legal research, and document drafting assistance",
      directory: "/legal",
      promptCount: 12,
      lastUpdated: "2 weeks ago",
      createdAt: "2023-12-20",
      isPublic: false
    },
    {
      id: 6,
      name: "Educational Tutor",
      description: "Teaching assistance, explanation generation, and learning support prompts",
      directory: "/education",
      promptCount: 28,
      lastUpdated: "3 weeks ago",
      createdAt: "2023-12-15",
      isPublic: true
    }
  ];

  const filteredProjects = projects.filter(project =>
    project.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    project.description.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const handleCreateProject = () => {
    console.log("Creating project:", newProject);
    setIsCreateDialogOpen(false);
    setNewProject({ name: "", description: "", directory: "" });
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Projects</h1>
          <p className="text-muted-foreground">Organize your prompts into projects</p>
        </div>
        <Dialog open={isCreateDialogOpen} onOpenChange={setIsCreateDialogOpen}>
          <DialogTrigger asChild>
            <Button>
              <Plus className="h-4 w-4 mr-2" />
              New Project
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Create New Project</DialogTitle>
              <DialogDescription>
                Organize your prompts by creating a new project
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-4">
              <div>
                <Label htmlFor="name">Project Name</Label>
                <Input
                  id="name"
                  value={newProject.name}
                  onChange={(e) => setNewProject({ ...newProject, name: e.target.value })}
                  placeholder="My Awesome Project"
                />
              </div>
              <div>
                <Label htmlFor="description">Description</Label>
                <Textarea
                  id="description"
                  value={newProject.description}
                  onChange={(e) => setNewProject({ ...newProject, description: e.target.value })}
                  placeholder="Describe what this project is for..."
                />
              </div>
              <div>
                <Label htmlFor="directory">Directory Path</Label>
                <Input
                  id="directory"
                  value={newProject.directory}
                  onChange={(e) => setNewProject({ ...newProject, directory: e.target.value })}
                  placeholder="/my-project"
                />
              </div>
              <div className="flex justify-end space-x-2">
                <Button variant="outline" onClick={() => setIsCreateDialogOpen(false)}>
                  Cancel
                </Button>
                <Button onClick={handleCreateProject}>
                  Create Project
                </Button>
              </div>
            </div>
          </DialogContent>
        </Dialog>
      </div>

      {/* Search and Filters */}
      <div className="flex items-center space-x-4">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search projects..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-10"
          />
        </div>
        <Button variant="outline">
          <Filter className="h-4 w-4 mr-2" />
          Filter
        </Button>
      </div>

      {/* Projects Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {filteredProjects.map((project) => (
          <Card key={project.id} className="hover:shadow-md transition-shadow cursor-pointer group">
            <CardHeader>
              <div className="flex items-start justify-between">
                <div className="flex items-center space-x-2">
                  <div className="h-8 w-8 rounded-lg bg-primary/10 flex items-center justify-center">
                    <Folder className="h-4 w-4 text-primary" />
                  </div>
                  <div>
                    <CardTitle className="group-hover:text-primary transition-colors">
                      {project.name}
                    </CardTitle>
                    {project.isPublic && (
                      <Badge variant="secondary" className="mt-1">Public</Badge>
                    )}
                  </div>
                </div>
                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <Button variant="ghost" size="sm">
                      <MoreHorizontal className="h-4 w-4" />
                    </Button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="end">
                    <DropdownMenuItem>Edit Project</DropdownMenuItem>
                    <DropdownMenuItem>View Prompts</DropdownMenuItem>
                    <DropdownMenuItem>Export</DropdownMenuItem>
                    <DropdownMenuItem className="text-destructive">Delete</DropdownMenuItem>
                  </DropdownMenuContent>
                </DropdownMenu>
              </div>
              <CardDescription>{project.description}</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="flex items-center justify-between text-sm">
                  <div className="flex items-center space-x-2 text-muted-foreground">
                    <FileText className="h-4 w-4" />
                    <span>{project.promptCount} prompts</span>
                  </div>
                  <div className="flex items-center space-x-2 text-muted-foreground">
                    <Calendar className="h-4 w-4" />
                    <span>{project.lastUpdated}</span>
                  </div>
                </div>
                <div className="pt-2 border-t">
                  <p className="text-xs text-muted-foreground">
                    Directory: <code className="bg-muted px-1 py-0.5 rounded">{project.directory}</code>
                  </p>
                  <p className="text-xs text-muted-foreground mt-1">
                    Created: {project.createdAt}
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {filteredProjects.length === 0 && (
        <div className="text-center py-12">
          <Folder className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
          <h3 className="text-lg font-semibold mb-2">No projects found</h3>
          <p className="text-muted-foreground mb-4">
            {searchQuery ? "Try adjusting your search terms" : "Create your first project to get started"}
          </p>
          {!searchQuery && (
            <Button onClick={() => setIsCreateDialogOpen(true)}>
              <Plus className="h-4 w-4 mr-2" />
              Create Project
            </Button>
          )}
        </div>
      )}
    </div>
  );
};

export default ProjectsPage;
