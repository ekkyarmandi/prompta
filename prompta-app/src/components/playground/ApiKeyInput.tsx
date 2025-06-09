
import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { ExternalLink } from "lucide-react";

interface ApiKeyInputProps {
  onApiKeySet: (apiKey: string) => void;
}

export const ApiKeyInput = ({ onApiKeySet }: ApiKeyInputProps) => {
  const [apiKey, setApiKey] = useState("");

  const handleSubmit = () => {
    if (apiKey.trim()) {
      localStorage.setItem("openrouter-api-key", apiKey.trim());
      onApiKeySet(apiKey.trim());
    }
  };

  return (
    <div className="space-y-4">
      <div className="space-y-2">
        <Label htmlFor="apiKey">OpenRouter API Key</Label>
        <Input
          id="apiKey"
          type="password"
          placeholder="sk-or-..."
          value={apiKey}
          onChange={(e) => setApiKey(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleSubmit()}
        />
      </div>
      
      <div className="flex items-center justify-between">
        <a
          href="https://openrouter.ai/keys"
          target="_blank"
          rel="noopener noreferrer"
          className="text-sm text-muted-foreground hover:text-primary flex items-center gap-1"
        >
          Get your API key <ExternalLink className="h-3 w-3" />
        </a>
        <Button onClick={handleSubmit} disabled={!apiKey.trim()}>
          Continue
        </Button>
      </div>
    </div>
  );
};
