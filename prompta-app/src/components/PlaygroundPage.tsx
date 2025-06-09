
import { useState, useEffect } from "react";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { ChatPlayground } from "./playground/ChatPlayground";
import { ComparePlayground } from "./playground/ComparePlayground";
import { ApiKeyInput } from "./playground/ApiKeyInput";

const PlaygroundPage = () => {
  const [openRouterApiKey, setOpenRouterApiKey] = useState<string>("");
  const [sharedPrompt, setSharedPrompt] = useState<string>("");

  // Check for stored prompt from PromptsPage on initial load
  useEffect(() => {
    const storedPrompt = localStorage.getItem("playground-prompt");
    if (storedPrompt) {
      const promptData = JSON.parse(storedPrompt);
      setSharedPrompt(promptData.content);
      localStorage.removeItem("playground-prompt"); // Clear after using
    }
  }, []);

  if (!openRouterApiKey) {
    return (
      <div className="container mx-auto py-4 px-4 sm:py-8">
        <div className="mb-6 sm:mb-8">
          <h1 className="text-2xl sm:text-3xl font-bold">Playground</h1>
          <p className="text-muted-foreground mt-2 text-sm sm:text-base">
            Test your prompts with different AI models using OpenRouter
          </p>
        </div>

        <Card className="max-w-md mx-auto">
          <CardHeader>
            <CardTitle className="text-lg sm:text-xl">OpenRouter API Key Required</CardTitle>
            <CardDescription className="text-sm">
              Enter your OpenRouter API key to start testing prompts with various AI models
            </CardDescription>
          </CardHeader>
          <CardContent>
            <ApiKeyInput onApiKeySet={setOpenRouterApiKey} />
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="container mx-auto py-4 px-4 sm:py-8">
      <div className="mb-6 sm:mb-8">
        <h1 className="text-2xl sm:text-3xl font-bold">Playground</h1>
        <p className="text-muted-foreground mt-2 text-sm sm:text-base">
          Test your prompts with different AI models
        </p>
      </div>

      <Tabs defaultValue="chat" className="space-y-4 sm:space-y-6">
        <TabsList className="grid w-full grid-cols-2 max-w-md">
          <TabsTrigger value="chat" className="text-sm">Chat</TabsTrigger>
          <TabsTrigger value="compare" className="text-sm">Compare</TabsTrigger>
        </TabsList>

        <TabsContent value="chat">
          <ChatPlayground 
            apiKey={openRouterApiKey} 
            sharedPrompt={sharedPrompt}
            onPromptChange={setSharedPrompt}
          />
        </TabsContent>

        <TabsContent value="compare">
          <ComparePlayground 
            apiKey={openRouterApiKey}
            sharedPrompt={sharedPrompt}
            onPromptChange={setSharedPrompt}
          />
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default PlaygroundPage;
