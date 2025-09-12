import React, { useEffect, useState } from 'react';
import { addComment, getPost } from '../services/community';
import { useParams } from 'react-router-dom';
import { getAuthToken } from '../services/auth';
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";

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

  if (!data) return (
    <div className="container mx-auto px-4 py-10 max-w-3xl">
      <Card>
        <CardContent className="p-6">불러오는 중...</CardContent>
      </Card>
    </div>
  );

  return (
    <div className="container mx-auto px-4 py-10 max-w-3xl space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>{data.post?.title}</CardTitle>
          <div className="text-sm text-muted-foreground">
            {data.post?.username} • {new Date(data.post?.created_at).toLocaleString()}
          </div>
        </CardHeader>
        <CardContent>
          <div className="whitespace-pre-wrap">{data.post?.content}</div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-xl">댓글</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {(data.comments || []).map((c: any) => (
            <Card key={c.id}>
              <CardContent className="p-4">
                <div className="text-sm text-muted-foreground mb-2">
                  {c.username} • {new Date(c.created_at).toLocaleString()}
                </div>
                <div className="whitespace-pre-wrap">{c.content}</div>
              </CardContent>
            </Card>
          ))}

          {loggedIn && (
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">댓글 작성</CardTitle>
              </CardHeader>
              <CardContent>
                <form onSubmit={onSubmit} className="space-y-4">
                  {error && (
                    <div className="p-3 bg-red-50 border border-red-200 text-red-700 rounded">
                      {error}
                    </div>
                  )}
                  <div className="space-y-2">
                    <Label htmlFor="comment">댓글 내용</Label>
                    <Textarea 
                      id="comment"
                      placeholder="댓글 내용을 입력하세요" 
                      value={content} 
                      onChange={e => setContent(e.target.value)} 
                      rows={3} 
                    />
                  </div>
                  <Button type="submit">댓글 등록</Button>
                </form>
              </CardContent>
            </Card>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

export default PostDetailPage;

