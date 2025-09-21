import { apiClient, extractErrorMessage } from '@/shared/api/client';

export type PostCategory = 'general' | 'strategy' | 'question' | 'news' | 'backtest_share';
export type PostContentType = 'text' | 'markdown';

export interface Author {
  id: number;
  username: string;
  email: string;
}

export interface PostSummary {
  id: number;
  category: PostCategory;
  title: string;
  viewCount: number;
  likeCount: number;
  commentCount: number;
  pinned: boolean;
  featured: boolean;
  createdAt: string;
  author: Author;
}

export interface PostDetail extends PostSummary {
  content: string;
  contentType: PostContentType;
  deleted: boolean;
  updatedAt: string;
}

export interface CommentItem {
  id: number;
  postId: number;
  parentId: number | null;
  content: string;
  likeCount: number;
  deleted: boolean;
  createdAt: string;
  updatedAt: string;
  author: Author;
  children: CommentItem[];
}

export interface PageResponse<T> {
  content: T[];
  totalElements: number;
  totalPages: number;
  size: number;
  number: number;
}

export interface ListPostsParams {
  page?: number;
  size?: number;
  category?: PostCategory | 'all';
  keyword?: string;
}

export interface CreatePostPayload {
  title: string;
  content: string;
  category: PostCategory;
  contentType?: PostContentType;
  pinned?: boolean;
  featured?: boolean;
}

export interface AddCommentPayload {
  parentId?: number | null;
  content: string;
}

export const listPosts = async (params: ListPostsParams = {}): Promise<PageResponse<PostSummary>> => {
  const query: Record<string, string> = {
    page: String(params.page ?? 0),
    size: String(params.size ?? 20),
  };
  if (params.category && params.category !== 'all') {
    query.category = params.category;
  }
  if (params.keyword) {
    query.keyword = params.keyword;
  }
  try {
    const { data } = await apiClient.get<PageResponse<PostSummary>>('/v1/community/posts', {
      params: query,
    });
    return data;
  } catch (err) {
    throw new Error(extractErrorMessage(err));
  }
};

export const getPost = async (postId: number): Promise<PostDetail> => {
  try {
    const { data } = await apiClient.get<PostDetail>(`/v1/community/posts/${postId}`);
    return data;
  } catch (err) {
    throw new Error(extractErrorMessage(err));
  }
};

export const createPost = async (payload: CreatePostPayload): Promise<PostDetail> => {
  try {
    const { data } = await apiClient.post<PostDetail>('/v1/community/posts', {
      ...payload,
      contentType: payload.contentType ?? 'markdown',
    });
    return data;
  } catch (err) {
    throw new Error(extractErrorMessage(err));
  }
};

export const togglePostLike = async (postId: number): Promise<{ liked: boolean }> => {
  try {
    const { data } = await apiClient.post<{ liked: boolean }>(`/v1/community/posts/${postId}/like`);
    return data;
  } catch (err) {
    throw new Error(extractErrorMessage(err));
  }
};

export const listComments = async (postId: number): Promise<CommentItem[]> => {
  try {
    const { data } = await apiClient.get<CommentItem[]>(`/v1/community/posts/${postId}/comments`);
    return data;
  } catch (err) {
    throw new Error(extractErrorMessage(err));
  }
};

export const addComment = async (postId: number, payload: AddCommentPayload): Promise<CommentItem> => {
  try {
    const { data } = await apiClient.post<CommentItem>(`/v1/community/posts/${postId}/comments`, {
      parentId: payload.parentId ?? null,
      content: payload.content,
    });
    return data;
  } catch (err) {
    throw new Error(extractErrorMessage(err));
  }
};

export const deleteComment = async (commentId: number): Promise<void> => {
  try {
    await apiClient.delete(`/v1/community/comments/${commentId}`);
  } catch (err) {
    throw new Error(extractErrorMessage(err));
  }
};
