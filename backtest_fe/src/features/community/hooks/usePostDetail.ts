import { useCallback, useEffect, useState } from 'react';
import { addComment, getPost } from '../services/community';

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
    try {
      const response = await getPost(postId);
      setData(response);
    } catch (err) {
      const message = err instanceof Error ? err.message : '게시글을 불러오지 못했습니다.';
      setError(message);
    } finally {
      setLoading(false);
    }
  }, [postId]);

  const submitComment = useCallback(
    async (content: string) => {
      if (!postId) return;
      try {
        await addComment(postId, content);
        await load();
      } catch (err) {
        const message = err instanceof Error ? err.message : '댓글 등록에 실패했습니다.';
        setError(message);
        throw err;
      }
    },
    [postId, load],
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
