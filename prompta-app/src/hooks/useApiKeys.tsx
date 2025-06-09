
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { supabase } from '@/integrations/supabase/client';
import { useAuth } from '@/components/auth/AuthProvider';
import { useOrganizations } from './useOrganizations';

export interface ApiKey {
  id: string;
  organization_id: string;
  name: string;
  key_prefix: string;
  permissions: string[];
  is_active: boolean;
  last_used_at: string | null;
  expires_at: string | null;
  created_by: string;
  created_at: string;
}

export const useApiKeys = () => {
  const { user } = useAuth();
  const { data: organizations } = useOrganizations();
  const currentOrgId = organizations?.[0]?.id; // Use first organization for now

  return useQuery({
    queryKey: ['api-keys', currentOrgId],
    queryFn: async () => {
      if (!user?.id || !currentOrgId) return [];
      
      const { data, error } = await supabase
        .from('api_keys')
        .select('*')
        .eq('organization_id', currentOrgId)
        .order('created_at', { ascending: false });

      if (error) throw error;
      return data || [];
    },
    enabled: !!user?.id && !!currentOrgId,
  });
};

export const useCreateApiKey = () => {
  const queryClient = useQueryClient();
  const { user } = useAuth();
  const { data: organizations } = useOrganizations();
  const currentOrgId = organizations?.[0]?.id;

  return useMutation({
    mutationFn: async ({ name, expiresAt }: { name: string; expiresAt?: string }) => {
      if (!user?.id || !currentOrgId) throw new Error('User or organization not found');

      // Generate a random API key
      const keyBytes = new Uint8Array(32);
      crypto.getRandomValues(keyBytes);
      const apiKey = 'pk_' + Array.from(keyBytes, byte => byte.toString(16).padStart(2, '0')).join('');
      
      // Create key prefix (first 8 characters)
      const keyPrefix = apiKey.substring(0, 8);
      
      // Hash the full key for storage (in a real implementation, use a proper hashing library)
      const keyHash = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(apiKey));
      const hashArray = Array.from(new Uint8Array(keyHash));
      const hashHex = hashArray.map(b => b.toString(16).padStart(2, '0')).join('');

      const { data, error } = await supabase
        .from('api_keys')
        .insert({
          organization_id: currentOrgId,
          name,
          key_hash: hashHex,
          key_prefix: keyPrefix,
          expires_at: expiresAt || null,
          created_by: user.id,
        })
        .select()
        .single();

      if (error) throw error;
      
      // Return both the database record and the actual key (only shown once)
      return { ...data, full_key: apiKey };
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['api-keys'] });
    },
  });
};

export const useUpdateApiKey = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ id, updates }: { id: string; updates: Partial<ApiKey> }) => {
      const { data, error } = await supabase
        .from('api_keys')
        .update(updates)
        .eq('id', id)
        .select()
        .single();

      if (error) throw error;
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['api-keys'] });
    },
  });
};

export const useDeleteApiKey = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (id: string) => {
      const { error } = await supabase
        .from('api_keys')
        .delete()
        .eq('id', id);

      if (error) throw error;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['api-keys'] });
    },
  });
};
