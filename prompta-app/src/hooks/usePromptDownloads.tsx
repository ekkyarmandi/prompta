
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { supabase } from "@/integrations/supabase/client";
import { useToast } from "@/hooks/use-toast";

export const usePromptDownloads = () => {
  const { toast } = useToast();
  const queryClient = useQueryClient();

  const downloadPrompt = useMutation({
    mutationFn: async (promptId: string) => {
      const { data: { user } } = await supabase.auth.getUser();
      if (!user) throw new Error("User not authenticated");

      const { error } = await supabase
        .from("prompt_downloads")
        .insert({
          prompt_id: promptId,
          user_id: user.id
        });

      if (error && error.code !== "23505") { // 23505 is unique constraint violation - expected for duplicate downloads
        throw error;
      }
    },
    onSuccess: () => {
      toast({
        title: "Prompt copied",
        description: "The prompt has been copied to your collection.",
      });
      queryClient.invalidateQueries({ queryKey: ["prompt-download-counts"] });
    },
    onError: (error) => {
      console.error("Copy error:", error);
      toast({
        title: "Copy failed",
        description: "Failed to copy prompt.",
        variant: "destructive",
      });
    },
  });

  return {
    downloadPrompt: downloadPrompt.mutate,
    isDownloading: downloadPrompt.isPending,
  };
};

export const usePromptDownloadCounts = () => {
  return useQuery({
    queryKey: ["prompt-download-counts"],
    queryFn: async () => {
      const { data, error } = await supabase
        .from("prompt_download_counts")
        .select("*");

      if (error) throw error;
      return data || [];
    },
  });
};
