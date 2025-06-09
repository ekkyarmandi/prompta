
import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Send, Loader2, Plus, X } from "lucide-react";

interface ComparePlaygroundProps {
  apiKey: string;
  sharedPrompt: string;
  onPromptChange: (prompt: string) => void;
}

interface ModelResponse {
  model: string;
  response: string;
  isLoading: boolean;
  error?: string;
}

const MODELS = [
  { id: "anthropic/claude-3.5-sonnet", name: "Claude 3.5 Sonnet" },
  { id: "openai/gpt-4", name: "GPT-4" },
  { id: "openai/gpt-3.5-turbo", name: "GPT-3.5 Turbo" },
  { id: "meta-llama/llama-2-70b-chat", name: "Llama 2 70B" },
];

export const ComparePlayground = ({ apiKey, sharedPrompt, onPromptChange }: ComparePlaygroundProps) => {
  const [input, setInput] = useState("");
  const [selectedModels, setSelectedModels] = useState<string[]>([MODELS[0].id, MODELS[1].id]);
  const [responses, setResponses] = useState<ModelResponse[]>([]);

  // Sync with shared prompt
  useEffect(() => {
    setInput(sharedPrompt);
  }, [sharedPrompt]);

  const handleInputChange = (value: string) => {
    setInput(value);
    onPromptChange(value);
  };

  const addModel = () => {
    if (selectedModels.length < 4) {
      const availableModel = MODELS.find(model => !selectedModels.includes(model.id));
      if (availableModel) {
        setSelectedModels([...selectedModels, availableModel.id]);
      }
    }
  };

  const removeModel = (modelId: string) => {
    if (selectedModels.length > 1) {
      setSelectedModels(selectedModels.filter(id => id !== modelId));
      setResponses(responses.filter(r => r.model !== modelId));
    }
  };

  const updateModel = (index: number, newModelId: string) => {
    const newSelectedModels = [...selectedModels];
    newSelectedModels[index] = newModelId;
    setSelectedModels(newSelectedModels);
  };

  const sendToAllModels = async () => {
    if (!input.trim()) return;

    // Initialize responses
    const initialResponses = selectedModels.map(model => ({
      model,
      response: "",
      isLoading: true,
    }));
    setResponses(initialResponses);

    // Send to all models simultaneously
    const promises = selectedModels.map(async (modelId) => {
      try {
        const response = await fetch("https://openrouter.ai/api/v1/chat/completions", {
          method: "POST",
          headers: {
            "Authorization": `Bearer ${apiKey}`,
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            model: modelId,
            messages: [{ role: "user", content: input }],
          }),
        });

        if (!response.ok) {
          throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        const data = await response.json();
        return {
          model: modelId,
          response: data.choices[0].message.content,
          isLoading: false,
        };
      } catch (error) {
        return {
          model: modelId,
          response: "",
          isLoading: false,
          error: error instanceof Error ? error.message : "Failed to get response",
        };
      }
    });

    // Update responses as they complete
    promises.forEach((promise, index) => {
      promise.then((result) => {
        setResponses(prev => prev.map(r => r.model === result.model ? result : r));
      });
    });
  };

  const clearResponses = () => {
    setResponses([]);
  };

  const getModelName = (modelId: string) => {
    return MODELS.find(m => m.id === modelId)?.name || modelId;
  };

  return (
    <div className="space-y-4 sm:space-y-6">
      {/* Input Section */}
      <Card>
        <CardHeader className="pb-3 sm:pb-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 sm:gap-4">
            <CardTitle className="text-lg sm:text-xl">Compare Models</CardTitle>
            <div className="flex flex-col sm:flex-row gap-2">
              {selectedModels.length < 4 && (
                <Button variant="outline" size="sm" onClick={addModel} className="w-full sm:w-auto">
                  <Plus className="h-4 w-4 mr-2" />
                  Add Model
                </Button>
              )}
              <Button variant="outline" size="sm" onClick={clearResponses} className="w-full sm:w-auto">
                Clear
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Model Selection */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
            {selectedModels.map((modelId, index) => (
              <div key={index} className="flex gap-2">
                <Select value={modelId} onValueChange={(value) => updateModel(index, value)}>
                  <SelectTrigger className="flex-1">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {MODELS.map((model) => (
                      <SelectItem key={model.id} value={model.id}>
                        {model.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                {selectedModels.length > 1 && (
                  <Button
                    variant="outline"
                    size="icon"
                    onClick={() => removeModel(modelId)}
                    className="shrink-0"
                  >
                    <X className="h-4 w-4" />
                  </Button>
                )}
              </div>
            ))}
          </div>

          {/* Input */}
          <div className="flex flex-col sm:flex-row gap-2">
            <Textarea
              placeholder="Enter your prompt to compare across models..."
              value={input}
              onChange={(e) => handleInputChange(e.target.value)}
              className="resize-none text-sm sm:text-base"
              rows={3}
            />
            <Button
              onClick={sendToAllModels}
              disabled={!input.trim() || responses.some(r => r.isLoading)}
              className="w-full sm:w-auto sm:self-end"
            >
              <Send className="h-4 w-4 mr-2" />
              Send to All
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Responses Grid */}
      {responses.length > 0 && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 sm:gap-6">
          {responses.map((response) => (
            <Card key={response.model} className="h-[400px] flex flex-col">
              <CardHeader className="border-b pb-3">
                <CardTitle className="text-base sm:text-lg">{getModelName(response.model)}</CardTitle>
              </CardHeader>
              <CardContent className="flex-1 p-0">
                <ScrollArea className="h-full p-3 sm:p-4">
                  {response.isLoading ? (
                    <div className="flex items-center justify-center py-8">
                      <div className="flex items-center gap-2">
                        <Loader2 className="h-4 w-4 animate-spin" />
                        <span className="text-sm sm:text-base">Generating response...</span>
                      </div>
                    </div>
                  ) : response.error ? (
                    <div className="text-destructive text-sm sm:text-base">
                      Error: {response.error}
                    </div>
                  ) : (
                    <div className="whitespace-pre-wrap text-sm sm:text-base">
                      {response.response}
                    </div>
                  )}
                </ScrollArea>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
};
