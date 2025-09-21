import { useCallback, useEffect, useState } from 'react';
import {
  addComment as addCommentApi,
  AddCommentPayload,
  CommentItem,
  getPost,
  listComments,
  PostDetail,
} from '../services/community';

export const usePostDetail = (postId: number | null | undefined) => {
  const [post, setPost] = useState<PostDetail | null>(null);
  const [comments, setComments] = useState<CommentItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    if (!postId) return;
    setLoading(true);
    setError(null);
    try {
      const [postResponse, commentsResponse] = await Promise.all([getPost(postId), listComments(postId)]);
      setPost(postResponse);
      setComments(commentsResponse);
    } catch (err) {
      const message = err instanceof Error ? err.message : '게시글을 불러오는 중 오류가 발생했습니다.';
      setError(message);
      setPost(null);
      setComments([]);
    } finally {
      setLoading(false);
    }
  }, [postId]);

  useEffect(() => {
    if (postId) {
      void load();
    }
  }, [load, postId]);

  const addComment = useCallback(
    async (payload: AddCommentPayload) => {
      if (!postId) {
        throw new Error('게시글이 선택되지 않았습니다.');
      }
      const newComment = await addCommentApi(postId, payload);
      // 최신 댓글을 다시 로드해 정합성을 유지
      const refreshed = await listComments(postId);
      setComments(refreshed);
      return newComment;
    },
    [postId]
  );

  return {
    data: post,
    comments,
    loading,
    error,
    reload: load,
    addComment,
    setError,
    setPost,
  };
};
