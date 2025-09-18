import { getAuthToken } from '@/features/auth/services/auth';

const getApiBase = () => (import.meta as any)?.env?.VITE_API_BASE_URL?.replace(/\/$/, '') || '';

export async function listPosts() {
  const res = await fetch(`${getApiBase()}/api/v1/community/posts`);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function createPost(title: string, content: string) {
  const token = getAuthToken();
  const res = await fetch(`${getApiBase()}/api/v1/community/posts`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': token ? `Bearer ${token}` : ''
    },
    body: JSON.stringify({ title, content })
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function getPost(postId: number) {
  const res = await fetch(`${getApiBase()}/api/v1/community/posts/${postId}`);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function addComment(postId: number, content: string) {
  const token = getAuthToken();
  const res = await fetch(`${getApiBase()}/api/v1/community/posts/${postId}/comments`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': token ? `Bearer ${token}` : ''
    },
    body: JSON.stringify({ content })
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

