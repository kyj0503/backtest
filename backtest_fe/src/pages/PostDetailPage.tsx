import React, { useMemo, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useAuth } from '@/features/auth/hooks/useAuth';
import { usePostDetail } from '@/features/community/hooks/usePostDetail';
import { CommentItem, togglePostLike } from '@/features/community/services/community';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/shared/ui/card';
import { Badge } from '@/shared/ui/badge';
import { Separator } from '@/shared/ui/separator';
import { toast } from 'sonner';
import { Loader2, MessageCirclePlus, ThumbsUp } from 'lucide-react';
import { Textarea } from '@/shared/ui/textarea';
import { Button } from '@/shared/ui/button';
import { useForm } from 'react-hook-form';
import { z } from 'zod';
import { zodResolver } from '@hookform/resolvers/zod';
import { formatRelative } from 'date-fns';

const commentSchema = z.object({
  content: z
    .string()
    .min(1, '댓글을 입력해주세요.')
    .max(1000, '댓글은 1000자 이하로 입력해주세요.'),
});

type CommentFormValues = z.infer<typeof commentSchema>;

const renderComment = (comment: CommentItem, depth = 0) => {
  const isDeleted = comment.deleted;
  return (
    <div key={comment.id} className="space-y-2">
      <div
        className="rounded-lg border border-border/80 bg-background px-3 py-2 shadow-sm"
        style={{ marginLeft: depth * 16 }}
      >
        <div className="flex items-center justify-between">
          <span className="text-sm font-semibold text-foreground">{comment.author.username}</span>
          <span className="text-xs text-muted-foreground">
            {formatRelative(new Date(comment.createdAt), new Date())}
          </span>
        </div>
        <p className="text-sm text-muted-foreground">
          {isDeleted ? '삭제된 댓글입니다.' : comment.content}
        </p>
      </div>
      {comment.children?.map((child) => renderComment(child, depth + 1))}
    </div>
  );
};

const PostDetailPage: React.FC = () => {
  const { postId } = useParams<{ postId: string }>();
  const numericId = postId ? Number(postId) : NaN;
  const { user } = useAuth();
  const navigate = useNavigate();
  const [likeLoading, setLikeLoading] = useState(false);

  const { data: post, comments, loading, error, reload, addComment } = usePostDetail(
    Number.isNaN(numericId) ? null : numericId
  );

  const form = useForm<CommentFormValues>({
    resolver: zodResolver(commentSchema),
    defaultValues: { content: '' },
  });

  const handleAddComment = form.handleSubmit(async (values) => {
    if (!post) return;
    if (!user) {
      toast.info('로그인 후 댓글을 작성할 수 있습니다.');
      return;
    }
    try {
      await addComment({ content: values.content });
      toast.success('댓글이 등록되었습니다.');
      form.reset();
      reload();
    } catch (err) {
      const message = err instanceof Error ? err.message : '댓글 작성 중 오류가 발생했습니다.';
      toast.error(message);
    }
  });

  const handleToggleLike = async () => {
    if (!post || !user) {
      toast.info('로그인 후 좋아요를 누를 수 있습니다.');
      return;
    }
    try {
      setLikeLoading(true);
      const response = await togglePostLike(post.id);
      toast.success(response.liked ? '게시글을 좋아합니다.' : '좋아요를 취소했습니다.');
      reload();
    } catch (error) {
      const message = error instanceof Error ? error.message : '좋아요 처리 중 오류가 발생했습니다.';
      toast.error(message);
    } finally {
      setLikeLoading(false);
    }
  };

  const renderedComments = useMemo(() => comments.map((comment) => renderComment(comment)), [comments]);

  if (Number.isNaN(numericId)) {
    return (
      <div className="container mx-auto max-w-3xl px-4 py-10">
        <p className="text-sm text-destructive">잘못된 게시글 경로입니다.</p>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="container mx-auto max-w-3xl px-4 py-10">
        <div className="flex items-center gap-2 text-muted-foreground">
          <Loader2 className="h-4 w-4 animate-spin" />
          <span className="text-sm">게시글을 불러오는 중입니다...</span>
        </div>
      </div>
    );
  }

  if (error || !post) {
    return (
      <div className="container mx-auto max-w-3xl px-4 py-10">
        <p className="text-sm text-destructive">{error ?? '게시글을 찾을 수 없습니다.'}</p>
        <Button variant="ghost" className="mt-3" onClick={() => navigate('/community')}>
          커뮤니티로 돌아가기
        </Button>
      </div>
    );
  }

  return (
    <div className="container mx-auto max-w-3xl space-y-8 px-4 py-10">
      <Card className="shadow-sm">
        <CardHeader className="space-y-4">
          <div className="flex items-center gap-2">
            <Badge variant="outline" className="rounded-full capitalize text-xs">
              {post.category}
            </Badge>
            {post.pinned && <Badge variant="secondary">고정</Badge>}
            {post.featured && <Badge variant="secondary">추천</Badge>}
          </div>
          <CardTitle className="text-2xl font-bold text-foreground">{post.title}</CardTitle>
          <CardDescription className="flex flex-wrap items-center gap-3 text-xs text-muted-foreground">
            <span>작성자 {post.author.username}</span>
            <span>{formatRelative(new Date(post.createdAt), new Date())}</span>
            <span>조회 {post.viewCount.toLocaleString()}</span>
            <span>좋아요 {post.likeCount.toLocaleString()}</span>
            <span>댓글 {post.commentCount.toLocaleString()}</span>
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <Separator />
          <div className="prose max-w-none whitespace-pre-wrap text-sm text-foreground">
            {post.content}
          </div>
          <div className="flex items-center justify-between">
            <Button variant="outline" onClick={() => navigate('/community')}>
              목록으로 돌아가기
            </Button>
            <Button
              variant={post.likeCount > 0 ? 'default' : 'secondary'}
              disabled={likeLoading}
              onClick={() => void handleToggleLike()}
              className="rounded-full"
            >
              {likeLoading ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <ThumbsUp className="mr-2 h-4 w-4" />}
              좋아요
            </Button>
          </div>
        </CardContent>
      </Card>

      <section className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-xl font-semibold">댓글</h2>
          <Badge variant="outline" className="rounded-full text-xs">
            {comments.length} 개의 댓글
          </Badge>
        </div>
        <Separator />
        <div className="space-y-4">{renderedComments}</div>
        {comments.length === 0 && (
          <div className="rounded-lg border border-dashed border-border/60 px-4 py-8 text-center text-sm text-muted-foreground">
            아직 댓글이 없습니다. 첫번째 댓글을 작성해보세요.
          </div>
        )}
      </section>

      <section className="rounded-lg border border-border/80 p-4 shadow-sm">
        <div className="flex items-center gap-2">
          <MessageCirclePlus className="h-5 w-5 text-primary" />
          <h3 className="text-lg font-semibold">댓글 작성</h3>
        </div>
        <p className="mt-1 text-xs text-muted-foreground">
          Markdown 문법은 지원되지 않으며, 최대 1000자까지 입력할 수 있습니다.
        </p>
        <form className="mt-4 space-y-3" onSubmit={handleAddComment}>
          <Textarea
            rows={4}
            placeholder={user ? '댓글을 입력해주세요.' : '로그인 후 댓글을 작성할 수 있습니다.'}
            disabled={!user || form.formState.isSubmitting}
            {...form.register('content')}
          />
          {form.formState.errors.content && (
            <p className="text-xs text-destructive">{form.formState.errors.content.message}</p>
          )}
          <div className="flex justify-end gap-2">
            <Button type="submit" disabled={!user || form.formState.isSubmitting}>
              {form.formState.isSubmitting && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              댓글 등록
            </Button>
          </div>
        </form>
      </section>
    </div>
  );
};

export default PostDetailPage;
