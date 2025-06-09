
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Chrome, Code, BookOpen, Terminal, Package, Download, ExternalLink } from "lucide-react";

const extensions = [
  {
    name: "Chrome Extension",
    description: "Access your prompts directly from any webpage. Perfect for content creation and quick prompt execution.",
    icon: Chrome,
    status: "Available",
    statusVariant: "default" as const,
    features: ["Quick prompt access", "Webpage integration", "One-click execution"],
    downloadUrl: "#",
    docsUrl: "#"
  },
  {
    name: "VS Code Extension",
    description: "Integrate prompts into your development workflow. Generate code, documentation, and more directly in your editor.",
    icon: Code,
    status: "Available",
    statusVariant: "default" as const,
    features: ["Code generation", "Inline prompts", "Snippet management"],
    downloadUrl: "#",
    docsUrl: "#"
  },
  {
    name: "Obsidian Plugin",
    description: "Seamlessly use prompts within your knowledge management system. Perfect for note-taking and research.",
    icon: BookOpen,
    status: "Beta",
    statusVariant: "secondary" as const,
    features: ["Note enhancement", "Research automation", "Template generation"],
    downloadUrl: "#",
    docsUrl: "#"
  },
  {
    name: "Model Context Protocol",
    description: "Connect with MCP-compatible applications and tools for advanced AI integrations.",
    icon: Terminal,
    status: "Coming Soon",
    statusVariant: "outline" as const,
    features: ["Tool integration", "Context sharing", "Advanced workflows"],
    downloadUrl: null,
    docsUrl: "#"
  },
  {
    name: "Command Line Interface",
    description: "Use prompts from your terminal. Automate workflows and integrate with scripts and CI/CD pipelines.",
    icon: Terminal,
    status: "Available",
    statusVariant: "default" as const,
    features: ["Terminal access", "Script integration", "Automation ready"],
    downloadUrl: "#",
    docsUrl: "#"
  },
  {
    name: "Python Library",
    description: "Integrate prompts into your Python applications and data science workflows.",
    icon: Package,
    status: "Available",
    statusVariant: "default" as const,
    features: ["Python integration", "Data science ready", "API access"],
    downloadUrl: "#",
    docsUrl: "#"
  }
];

const ExtensionsPage = () => {
  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Extensions & Integrations</h1>
        <p className="text-muted-foreground mt-2">
          Connect Prompta with your favorite tools and workflows. Access your prompts wherever you work.
        </p>
      </div>

      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        {extensions.map((extension) => {
          const IconComponent = extension.icon;
          return (
            <Card key={extension.name} className="relative">
              <CardHeader>
                <div className="flex items-start justify-between">
                  <div className="flex items-center space-x-3">
                    <div className="p-2 bg-primary/10 rounded-lg">
                      <IconComponent className="h-6 w-6" />
                    </div>
                    <div>
                      <CardTitle className="text-lg">{extension.name}</CardTitle>
                      <Badge variant={extension.statusVariant} className="mt-1">
                        {extension.status}
                      </Badge>
                    </div>
                  </div>
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                <CardDescription className="text-sm leading-relaxed">
                  {extension.description}
                </CardDescription>
                
                <div className="space-y-2">
                  <h4 className="text-sm font-medium">Key Features:</h4>
                  <ul className="text-sm text-muted-foreground space-y-1">
                    {extension.features.map((feature, index) => (
                      <li key={index} className="flex items-center space-x-2">
                        <div className="h-1.5 w-1.5 rounded-full bg-primary" />
                        <span>{feature}</span>
                      </li>
                    ))}
                  </ul>
                </div>

                <div className="flex gap-2 pt-2">
                  {extension.downloadUrl && (
                    <Button size="sm" className="flex-1">
                      <Download className="h-4 w-4 mr-2" />
                      Install
                    </Button>
                  )}
                  <Button variant="outline" size="sm" className={extension.downloadUrl ? "" : "flex-1"}>
                    <ExternalLink className="h-4 w-4 mr-2" />
                    Docs
                  </Button>
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Need a Custom Integration?</CardTitle>
          <CardDescription>
            Don't see the tool you need? We're constantly adding new integrations and would love to hear from you.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Button>
            <ExternalLink className="h-4 w-4 mr-2" />
            Request Integration
          </Button>
        </CardContent>
      </Card>
    </div>
  );
};

export default ExtensionsPage;
