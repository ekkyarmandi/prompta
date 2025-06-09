
import { useState } from "react";
import { Plus, Key, Copy, MoreHorizontal, Eye, EyeOff, Trash } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from "@/components/ui/dropdown-menu";
import { AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle, AlertDialogTrigger } from "@/components/ui/alert-dialog";
import { useToast } from "@/hooks/use-toast";
import { Switch } from "@/components/ui/switch";
import { useApiKeys, useCreateApiKey, useUpdateApiKey, useDeleteApiKey } from "@/hooks/useApiKeys";

const ApiKeysPage = () => {
  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false);
  const [visibleKeys, setVisibleKeys] = useState<Set<string>>(new Set());
  const [newlyCreatedKey, setNewlyCreatedKey] = useState<string | null>(null);
  const [newApiKey, setNewApiKey] = useState({
    name: "",
    expiresAt: ""
  });
  const { toast } = useToast();

  const { data: apiKeys = [], isLoading } = useApiKeys();
  const createApiKeyMutation = useCreateApiKey();
  const updateApiKeyMutation = useUpdateApiKey();
  const deleteApiKeyMutation = useDeleteApiKey();

  const toggleKeyVisibility = (keyId: string) => {
    setVisibleKeys(prev => {
      const newSet = new Set(prev);
      if (newSet.has(keyId)) {
        newSet.delete(keyId);
      } else {
        newSet.add(keyId);
      }
      return newSet;
    });
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    toast({
      title: "Copied to clipboard",
      description: "API key has been copied to your clipboard.",
    });
  };

  const maskKey = (prefix: string) => {
    return `${prefix}${"•".repeat(32)}`;
  };

  const handleCreateApiKey = async () => {
    try {
      const result = await createApiKeyMutation.mutateAsync({
        name: newApiKey.name,
        expiresAt: newApiKey.expiresAt || undefined,
      });
      
      setNewlyCreatedKey(result.full_key);
      setIsCreateDialogOpen(false);
      setNewApiKey({ name: "", expiresAt: "" });
      
      toast({
        title: "API Key Created",
        description: "Your new API key has been generated successfully. Make sure to copy it now - it won't be shown again.",
      });
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to create API key. Please try again.",
        variant: "destructive",
      });
    }
  };

  const handleToggleActive = async (keyId: string, isActive: boolean) => {
    try {
      await updateApiKeyMutation.mutateAsync({
        id: keyId,
        updates: { is_active: !isActive }
      });
      
      toast({
        title: isActive ? "API Key Disabled" : "API Key Enabled",
        description: `The API key has been ${isActive ? 'disabled' : 'enabled'}.`,
      });
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to update API key status.",
        variant: "destructive",
      });
    }
  };

  const handleDeleteKey = async (keyId: string) => {
    try {
      await deleteApiKeyMutation.mutateAsync(keyId);
      toast({
        title: "API Key Deleted",
        description: "The API key has been permanently deleted.",
        variant: "destructive",
      });
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to delete API key.",
        variant: "destructive",
      });
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString();
  };

  const getTimeAgo = (dateString: string | null) => {
    if (!dateString) return "Never";
    
    const now = new Date();
    const date = new Date(dateString);
    const diffInMinutes = Math.floor((now.getTime() - date.getTime()) / (1000 * 60));
    
    if (diffInMinutes < 60) return `${diffInMinutes} minutes ago`;
    if (diffInMinutes < 1440) return `${Math.floor(diffInMinutes / 60)} hours ago`;
    return `${Math.floor(diffInMinutes / 1440)} days ago`;
  };

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold">API Keys</h1>
            <p className="text-muted-foreground">Manage your API keys for programmatic access</p>
          </div>
        </div>
        <div className="text-center py-12">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent mx-auto mb-4"></div>
          <p className="text-muted-foreground">Loading API keys...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Newly Created Key Display */}
      {newlyCreatedKey && (
        <Card className="border-green-200 bg-green-50">
          <CardHeader>
            <CardTitle className="text-green-800">🎉 API Key Created Successfully!</CardTitle>
            <CardDescription className="text-green-700">
              Make sure to copy your API key now. You won't be able to see it again!
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="bg-white p-3 rounded-lg border">
              <div className="flex items-center justify-between">
                <code className="text-sm font-mono text-green-800">{newlyCreatedKey}</code>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => {
                    copyToClipboard(newlyCreatedKey);
                    setNewlyCreatedKey(null);
                  }}
                >
                  <Copy className="h-4 w-4 mr-2" />
                  Copy & Close
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">API Keys</h1>
          <p className="text-muted-foreground">Manage your API keys for programmatic access</p>
        </div>
        <Dialog open={isCreateDialogOpen} onOpenChange={setIsCreateDialogOpen}>
          <DialogTrigger asChild>
            <Button>
              <Plus className="h-4 w-4 mr-2" />
              Generate API Key
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Generate New API Key</DialogTitle>
              <DialogDescription>
                Create a new API key for accessing your prompts programmatically
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-4">
              <div>
                <Label htmlFor="key-name">API Key Name</Label>
                <Input
                  id="key-name"
                  value={newApiKey.name}
                  onChange={(e) => setNewApiKey({ ...newApiKey, name: e.target.value })}
                  placeholder="Production API, Development, etc."
                />
              </div>
              <div>
                <Label htmlFor="expires-at">Expiration Date (Optional)</Label>
                <Input
                  id="expires-at"
                  type="date"
                  value={newApiKey.expiresAt}
                  onChange={(e) => setNewApiKey({ ...newApiKey, expiresAt: e.target.value })}
                />
                <p className="text-xs text-muted-foreground mt-1">
                  Leave empty for no expiration
                </p>
              </div>
              <div className="bg-muted/50 p-4 rounded-lg">
                <h4 className="font-semibold mb-2">⚠️ Important Security Notice</h4>
                <ul className="text-sm text-muted-foreground space-y-1">
                  <li>• This key will only be shown once upon creation</li>
                  <li>• Store it securely and never share it publicly</li>
                  <li>• Use different keys for different environments</li>
                  <li>• Regularly rotate your API keys</li>
                </ul>
              </div>
              <div className="flex justify-end space-x-2">
                <Button variant="outline" onClick={() => setIsCreateDialogOpen(false)}>
                  Cancel
                </Button>
                <Button 
                  onClick={handleCreateApiKey}
                  disabled={!newApiKey.name.trim() || createApiKeyMutation.isPending}
                >
                  {createApiKeyMutation.isPending ? "Generating..." : "Generate Key"}
                </Button>
              </div>
            </div>
          </DialogContent>
        </Dialog>
      </div>

      {/* API Keys List */}
      <div className="space-y-4">
        {apiKeys.map((apiKey) => (
          <Card key={apiKey.id} className="hover:shadow-md transition-shadow">
            <CardHeader>
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  <div className="h-10 w-10 rounded-lg bg-primary/10 flex items-center justify-center">
                    <Key className="h-5 w-5 text-primary" />
                  </div>
                  <div>
                    <CardTitle className="flex items-center space-x-2">
                      <span>{apiKey.name}</span>
                      <Badge variant={apiKey.is_active ? "default" : "secondary"}>
                        {apiKey.is_active ? "Active" : "Inactive"}
                      </Badge>
                    </CardTitle>
                    <CardDescription>
                      Created on {formatDate(apiKey.created_at)} • Last used {getTimeAgo(apiKey.last_used_at)}
                    </CardDescription>
                  </div>
                </div>
                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <Button variant="ghost" size="sm">
                      <MoreHorizontal className="h-4 w-4" />
                    </Button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="end">
                    <DropdownMenuItem onClick={() => toggleKeyVisibility(apiKey.id)}>
                      {visibleKeys.has(apiKey.id) ? (
                        <>
                          <EyeOff className="h-4 w-4 mr-2" />
                          Hide Key
                        </>
                      ) : (
                        <>
                          <Eye className="h-4 w-4 mr-2" />
                          Show Key
                        </>
                      )}
                    </DropdownMenuItem>
                    <DropdownMenuItem onClick={() => copyToClipboard(apiKey.key_prefix + "...")}>
                      <Copy className="h-4 w-4 mr-2" />
                      Copy Prefix
                    </DropdownMenuItem>
                    <AlertDialog>
                      <AlertDialogTrigger asChild>
                        <DropdownMenuItem onSelect={(e) => e.preventDefault()} className="text-destructive">
                          <Trash className="h-4 w-4 mr-2" />
                          Delete Key
                        </DropdownMenuItem>
                      </AlertDialogTrigger>
                      <AlertDialogContent>
                        <AlertDialogHeader>
                          <AlertDialogTitle>Delete API Key</AlertDialogTitle>
                          <AlertDialogDescription>
                            Are you sure you want to delete "{apiKey.name}"? This action cannot be undone and will immediately revoke access for any applications using this key.
                          </AlertDialogDescription>
                        </AlertDialogHeader>
                        <AlertDialogFooter>
                          <AlertDialogCancel>Cancel</AlertDialogCancel>
                          <AlertDialogAction 
                            onClick={() => handleDeleteKey(apiKey.id)} 
                            className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
                          >
                            Delete Key
                          </AlertDialogAction>
                        </AlertDialogFooter>
                      </AlertDialogContent>
                    </AlertDialog>
                  </DropdownMenuContent>
                </DropdownMenu>
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="bg-muted/50 p-3 rounded-lg">
                  <div className="flex items-center justify-between">
                    <code className="text-sm font-mono">
                      {visibleKeys.has(apiKey.id) ? apiKey.key_prefix + "..." : maskKey(apiKey.key_prefix)}
                    </code>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => copyToClipboard(apiKey.key_prefix + "...")}
                    >
                      <Copy className="h-4 w-4" />
                    </Button>
                  </div>
                </div>

                <div className="grid grid-cols-3 gap-4 text-sm">
                  <div>
                    <p className="text-muted-foreground">Permissions</p>
                    <p className="font-semibold">{apiKey.permissions?.join(", ") || "read"}</p>
                  </div>
                  <div>
                    <p className="text-muted-foreground">Expires</p>
                    <p className="font-semibold">
                      {apiKey.expires_at ? formatDate(apiKey.expires_at) : "Never"}
                    </p>
                  </div>
                  <div>
                    <p className="text-muted-foreground">Status</p>
                    <div className="flex items-center space-x-2">
                      <Switch 
                        checked={apiKey.is_active} 
                        onCheckedChange={() => handleToggleActive(apiKey.id, apiKey.is_active)}
                      />
                      <span className="font-semibold">
                        {apiKey.is_active ? "Active" : "Disabled"}
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {apiKeys.length === 0 && (
        <div className="text-center py-12">
          <Key className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
          <h3 className="text-lg font-semibold mb-2">No API keys yet</h3>
          <p className="text-muted-foreground mb-4">
            Create your first API key to access your prompts programmatically
          </p>
          <Button onClick={() => setIsCreateDialogOpen(true)}>
            <Plus className="h-4 w-4 mr-2" />
            Generate API Key
          </Button>
        </div>
      )}

      {/* Usage Information */}
      <Card>
        <CardHeader>
          <CardTitle>API Usage Guidelines</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <h4 className="font-semibold mb-2">Authentication</h4>
              <code className="text-sm bg-muted p-2 rounded block">
                X-API-Key: your_api_key_here
              </code>
            </div>
            <div>
              <h4 className="font-semibold mb-2">Base URL</h4>
              <code className="text-sm bg-muted p-2 rounded block">
                https://api.prompta.dev/v1
              </code>
            </div>
          </div>
          <div>
            <h4 className="font-semibold mb-2">Example Request</h4>
            <pre className="text-sm bg-muted p-3 rounded overflow-x-auto">
{`curl -H "X-API-Key: your_api_key_here" \\
     https://api.prompta.dev/v1/prompts`}
            </pre>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default ApiKeysPage;
