import React, { useEffect, useState } from 'react';
import { listPosts, createPost } from '../services/community';
import { getAuthToken } from '../services/auth';

const CommunityPage: React.FC = () => {
  const [items, setItems] = useState<any[]>([]);
  const [title, setTitle] = useState('');
  const [content, setContent] = useState('');
  const [error, setError] = useState<string | null>(null);

  const load = async () => {
    try {
      const res = await listPosts();
      setItems(res.items || []);
    } catch (err: any) {
      setError(err?.message || '목록을 불러오지 못했습니다.');
    }
  };

  useEffect(() => { load(); }, []);

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    try {
      await createPost(title, content);
      setTitle('');
      setContent('');
      await load();
    } catch (err: any) {
      setError(err?.message || '등록 실패');
    }
  };

  const loggedIn = !!getAuthToken();

  return (
    <div className="container mx-auto px-4 py-10 max-w-4xl">
      <h2 className="text-2xl font-bold mb-6">커뮤니티</h2>
      {error && <div className="p-3 bg-red-50 border border-red-200 text-red-700 rounded mb-4">{error}</div>}

      {loggedIn && (
        <form onSubmit={onSubmit} className="bg-white border rounded p-4 mb-8 space-y-3">
          <input className="w-full px-3 py-2 border rounded" placeholder="제목" value={title} onChange={e => setTitle(e.target.value)} />
          <textarea className="w-full px-3 py-2 border rounded" placeholder="내용" value={content} onChange={e => setContent(e.target.value)} rows={4} />
          <button className="bg-blue-600 text-white rounded px-4 py-2">게시</button>
        </form>
      )}

      <div className="space-y-4">
        {items.map((it) => (
          <div key={it.id} className="bg-white border rounded p-4">
            <div className="text-sm text-gray-500 mb-1">{it.username} • {new Date(it.created_at).toLocaleString()}</div>
            <div className="text-lg font-semibold">{it.title}</div>
            <div className="text-gray-700 mt-2 whitespace-pre-wrap">{it.excerpt}</div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default CommunityPage;

