import React, { useEffect, useState } from 'react';
import { addComment, getPost } from '../services/community';
import { useParams } from 'react-router-dom';
import { getAuthToken } from '../services/auth';

const PostDetailPage: React.FC = () => {
  const { id } = useParams();
  const postId = Number(id);
  const [data, setData] = useState<any | null>(null);
  const [content, setContent] = useState('');
  const [error, setError] = useState<string | null>(null);

  const load = async () => {
    try {
      const res = await getPost(postId);
      setData(res);
    } catch (err: any) {
      setError(err?.message || '불러오기 실패');
    }
  };

  useEffect(() => { if (!isNaN(postId)) load(); }, [postId]);

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    try {
      await addComment(postId, content);
      setContent('');
      await load();
    } catch (err: any) {
      setError(err?.message || '등록 실패');
    }
  };

  const loggedIn = !!getAuthToken();

  if (!data) return (<div className="container mx-auto px-4 py-10 max-w-3xl">불러오는 중...</div>);

  return (
    <div className="container mx-auto px-4 py-10 max-w-3xl">
      <h2 className="text-2xl font-bold mb-2">{data.post?.title}</h2>
      <div className="text-sm text-gray-500 mb-6">{data.post?.username} • {new Date(data.post?.created_at).toLocaleString()}</div>
      <div className="bg-white border rounded p-4 whitespace-pre-wrap mb-8">{data.post?.content}</div>

      <h3 className="text-xl font-semibold mb-3">댓글</h3>
      <div className="space-y-3 mb-6">
        {(data.comments || []).map((c: any) => (
          <div key={c.id} className="bg-white border rounded p-3">
            <div className="text-sm text-gray-500 mb-1">{c.username} • {new Date(c.created_at).toLocaleString()}</div>
            <div className="whitespace-pre-wrap">{c.content}</div>
          </div>
        ))}
      </div>

      {loggedIn && (
        <form onSubmit={onSubmit} className="bg-white border rounded p-4 space-y-3">
          {error && <div className="p-3 bg-red-50 border border-red-200 text-red-700 rounded">{error}</div>}
          <textarea className="w-full px-3 py-2 border rounded" placeholder="댓글 내용" value={content} onChange={e => setContent(e.target.value)} rows={3} />
          <button className="bg-blue-600 text-white rounded px-4 py-2">댓글 등록</button>
        </form>
      )}
    </div>
  );
};

export default PostDetailPage;

