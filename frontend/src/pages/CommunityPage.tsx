import React, { useEffect, useState } from 'react';
import { listPosts, createPost } from '../services/community';
import { Link } from 'react-router-dom';
import { getAuthToken } from '../services/auth';
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";

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
      <Card>
        <CardHeader>
          <CardTitle>커뮤니티</CardTitle>
        </CardHeader>
        <CardContent className="space-y-6">
          {error && (
            <div className="p-3 bg-red-50 border border-red-200 text-red-700 rounded">
              {error}
            </div>
          )}

          {loggedIn && (
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">새 게시글 작성</CardTitle>
              </CardHeader>
              <CardContent>
                <form onSubmit={onSubmit} className="space-y-4">
                  <div className="space-y-2">
                    <Label htmlFor="title">제목</Label>
                    <Input 
                      id="title"
                      placeholder="제목을 입력하세요" 
                      value={title} 
                      onChange={e => setTitle(e.target.value)} 
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="content">내용</Label>
                    <Textarea 
                      id="content"
                      placeholder="내용을 입력하세요" 
                      value={content} 
                      onChange={e => setContent(e.target.value)} 
                      rows={4} 
                    />
                  </div>
                  <Button type="submit">게시</Button>
                </form>
              </CardContent>
            </Card>
          )}

          <div className="space-y-4">
            {items.map((it) => (
              <Link key={it.id} to={`/community/${it.id}`}>
                <Card className="hover:bg-accent/50 transition-colors">
                  <CardContent className="p-4">
                    <div className="text-sm text-muted-foreground mb-1">
                      {it.username} • {new Date(it.created_at).toLocaleString()}
                    </div>
                    <div className="text-lg font-semibold">{it.title}</div>
                    <div className="text-muted-foreground mt-2 whitespace-pre-wrap">
                      {it.excerpt}
                    </div>
                  </CardContent>
                </Card>
              </Link>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default CommunityPage;
