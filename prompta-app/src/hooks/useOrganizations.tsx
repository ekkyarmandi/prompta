
import { useQuery } from '@tanstack/react-query';
import { supabase } from '@/integrations/supabase/client';
import { useAuth } from '@/components/auth/AuthProvider';

export const useOrganizations = () => {
  const { user } = useAuth();

  return useQuery({
    queryKey: ['organizations', user?.id],
    queryFn: async () => {
      if (!user?.id) return [];
      
      const { data, error } = await supabase
        .from('organizations')
        .select(`
          *,
          organization_memberships!inner(
            role,
            joined_at
          )
        `)
        .eq('organization_memberships.user_id', user.id)
        .not('organization_memberships.joined_at', 'is', null);

      if (error) throw error;
      return data || [];
    },
    enabled: !!user?.id,
  });
};
