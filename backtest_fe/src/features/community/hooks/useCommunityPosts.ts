import { useCallback, useEffect, useState } from 'react';
import { listPosts } from '../services/community';

interface CommunityPost {
  id: number;
  title: string;
  content: string;
  excerpt?: string;
  view_count: number;
  like_count: number;
  created_at: string;
  username?: string;
}

interface UseCommunityPostsOptions {
  autoLoad?: boolean;
}

export const useCommunityPosts = ({ autoLoad = true }: UseCommunityPostsOptions = {}) => {
  const [posts, setPosts] = useState<CommunityPost[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const response = await listPosts();
      setPosts(response.items ?? []);
      setError('커뮤니티 기능은 현재 비활성화되어 있습니다.');
    } catch (err) {
      const message = err instanceof Error ? err.message : '커뮤니티 기능은 현재 비활성화되어 있습니다.';
      setError(message);
      setPosts([]);
    } finally {
      setLoading(false);
    }
  }, []);

  const submitPost = useCallback(async () => {
    const message = '커뮤니티 기능은 현재 비활성화되어 있습니다.';
    setError(message);
    throw new Error(message);
  }, []);

  useEffect(() => {
    if (autoLoad) {
      void load();
    }
  }, [autoLoad, load]);

  return {
    posts,
    loading,
    error,
    actions: {
      reload: load,
      createPost: submitPost,
      clearError: () => setError(null),
    },
  };
};
