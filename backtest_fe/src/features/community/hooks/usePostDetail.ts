import { useCallback, useEffect, useState } from 'react';
interface CommentItem {
  id: number;
  content: string;
  created_at: string;
  username?: string;
}

interface PostDetail {
  post: {
    id: number;
    title: string;
    content: string;
    view_count: number;
    like_count: number;
    created_at: string;
    username?: string;
  };
  comments: CommentItem[];
}

export const usePostDetail = (postId: number | null) => {
  const [data, setData] = useState<PostDetail | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    if (!postId) return;
    setLoading(true);
    setError(null);
    setData(null);
    setError('커뮤니티 기능은 현재 비활성화되어 있습니다.');
    setLoading(false);
  }, [postId]);

  const submitComment = useCallback(
    async () => {
      if (!postId) return;
      const message = '커뮤니티 기능은 현재 비활성화되어 있습니다.';
      setError(message);
      throw new Error(message);
    },
    [postId],
  );

  useEffect(() => {
    void load();
  }, [load]);

  return {
    data,
    loading,
    error,
    actions: {
      reload: load,
      addComment: submitComment,
      clearError: () => setError(null),
    },
  };
};
