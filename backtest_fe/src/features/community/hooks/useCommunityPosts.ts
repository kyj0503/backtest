import { useCallback, useEffect, useState } from 'react';
import { listPosts, ListPostsParams, PageResponse, PostSummary } from '../services/community';

interface UseCommunityPostsOptions {
  autoLoad?: boolean;
}

export const useCommunityPosts = (
  params: ListPostsParams,
  { autoLoad = true }: UseCommunityPostsOptions = {}
) => {
  const { page = 0, size = 20, category, keyword } = params;
  const [data, setData] = useState<PageResponse<PostSummary> | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(
    async (override?: ListPostsParams) => {
      setLoading(true);
      setError(null);
      try {
        const response = await listPosts({
          page,
          size,
          category,
          keyword,
          ...override,
        });
        setData(response);
      } catch (err) {
        const message = err instanceof Error ? err.message : '게시글을 불러오는 중 오류가 발생했습니다.';
        setError(message);
        setData(null);
      } finally {
        setLoading(false);
      }
    },
    [category, keyword, page, size]
  );

  useEffect(() => {
    if (autoLoad) {
      void load();
    }
  }, [autoLoad, load]);

  return {
    data,
    loading,
    error,
    reload: load,
    setError,
  };
};
