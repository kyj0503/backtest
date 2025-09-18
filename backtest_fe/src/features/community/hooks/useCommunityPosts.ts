import { useCallback, useEffect, useState } from 'react';
import { createPost, listPosts } from '../services/community';

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
    setError(null);
    try {
      const response = await listPosts();
      setPosts(response.items ?? []);
    } catch (err) {
      const message = err instanceof Error ? err.message : '목록을 불러오지 못했습니다.';
      setError(message);
    } finally {
      setLoading(false);
    }
  }, []);

  const submitPost = useCallback(async (title: string, content: string) => {
    setError(null);
    try {
      await createPost(title, content);
      await load();
    } catch (err) {
      const message = err instanceof Error ? err.message : '게시글 등록에 실패했습니다.';
      setError(message);
      throw err;
    }
  }, [load]);

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
