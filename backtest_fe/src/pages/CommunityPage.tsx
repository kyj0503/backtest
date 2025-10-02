import React, { useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '@/features/auth/hooks/useAuth';
import { useCommunityPosts } from '@/features/community/hooks/useCommunityPosts';
import {
  createPost,
  PostCategory,
  PostSummary,
  PostContentType,
} from '@/features/community/services/community';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/shared/ui/card';
import { Button } from '@/shared/ui/button';
import { Badge } from '@/shared/ui/badge';
import { Separator } from '@/shared/ui/separator';
import { Input } from '@/shared/ui/input';
import { Textarea } from '@/shared/ui/textarea';
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/shared/ui/dialog';
import { Alert, AlertDescription, AlertTitle } from '@/shared/ui/alert';
import { Pagination, PaginationContent, PaginationItem, PaginationNext, PaginationPrevious } from '@/shared/ui/pagination';
import { Label } from '@/shared/ui/label';
import { toast } from 'sonner';
import { useForm } from 'react-hook-form';
import { z } from 'zod';
import { zodResolver } from '@hookform/resolvers/zod';
import { Loader2, PenSquare } from 'lucide-react';
import { Link } from 'react-router-dom';
import { formatRelative } from 'date-fns';

const categoryOptions: { value: 'all' | PostCategory; label: string }[] = [
  { value: 'all', label: '전체' },
  { value: 'general', label: '자유' },
  { value: 'strategy', label: '전략 공유' },
  { value: 'question', label: '질문' },
  { value: 'news', label: '뉴스' },
  { value: 'backtest_share', label: '백테스트 공유' },
];

const contentTypeOptions: { value: PostContentType; label: string }[] = [
  { value: 'markdown', label: 'Markdown' },
  { value: 'text', label: 'Plain Text' },
];

const createPostSchema = z.object({
  title: z.string().min(3, '제목은 최소 3자 이상 입력해주세요.').max(200, '제목은 200자 이하로 입력해주세요.'),
  content: z.string().min(1, '내용을 입력해주세요.'),
  category: z.enum(['general', 'strategy', 'question', 'news', 'backtest_share']),
  contentType: z.enum(['text', 'markdown']),
  pinned: z.boolean().optional(),
  featured: z.boolean().optional(),
});

const CommunityPage: React.FC = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [category, setCategory] = useState<'all' | PostCategory>('all');
  const [keyword, setKeyword] = useState('');
  const [page, setPage] = useState(0);
  const pageSize = 10;

  const { data, loading, error, reload } = useCommunityPosts({
    page,
    size: pageSize,
    category,
    keyword: keyword.trim() ? keyword.trim() : undefined,
  });

  const totalPages = data?.totalPages ?? 0;

  const form = useForm<z.infer<typeof createPostSchema>>({
    resolver: zodResolver(createPostSchema),
    defaultValues: {
      title: '',
      content: '',
      category: 'general',
      contentType: 'markdown',
      pinned: false,
      featured: false,
    },
  });

  const [dialogOpen, setDialogOpen] = useState(false);
  const isSubmitting = form.formState.isSubmitting;

  const handleSubmit = form.handleSubmit(async (values) => {
    try {
      const created = await createPost({
        title: values.title,
        content: values.content,
        category: values.category,
        contentType: values.contentType,
        pinned: values.pinned,
        featured: values.featured,
      });
      toast.success('게시글이 등록되었습니다.');
      setDialogOpen(false);
      form.reset();
      reload({ page: 0 });
      navigate(`/community/${created.id}`);
    } catch (err) {
      const message = err instanceof Error ? err.message : '게시글 작성 중 오류가 발생했습니다.';
      toast.error(message);
    }
  });

  const handleSearch = (event: React.FormEvent) => {
    event.preventDefault();
    setPage(0);
    reload({ page: 0 });
  };

  const renderPostCard = (post: PostSummary) => (
    <Card
      key={post.id}
      className="transition hover:border-primary/50 hover:shadow-md"
    >
      <CardHeader className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <div className="flex items-center gap-2">
            <Badge variant="outline" className="rounded-full capitalize text-xs">
              {post.category}
            </Badge>
            {post.pinned && <Badge variant="secondary">고정</Badge>}
            {post.featured && <Badge variant="secondary">추천</Badge>}
          </div>
          <CardTitle className="mt-2 text-lg font-semibold">
            <Link to={`/community/${post.id}`} className="text-primary hover:underline">
              {post.title}
            </Link>
          </CardTitle>
          <CardDescription className="text-xs">
            작성자 {post.author.username} · {formatRelative(new Date(post.createdAt), new Date())}
          </CardDescription>
        </div>
        <div className="flex items-center gap-3 text-xs text-muted-foreground">
          <span>조회 {post.viewCount.toLocaleString()}</span>
          <span>좋아요 {post.likeCount.toLocaleString()}</span>
          <span>댓글 {post.commentCount.toLocaleString()}</span>
        </div>
      </CardHeader>
      <CardContent>
        <p className="line-clamp-3 text-sm text-muted-foreground">
          {post.commentCount > 0
            ? '댓글이 활발한 게시글입니다. 자세한 내용은 게시글에서 확인해보세요.'
            : '게시글의 전체 내용을 확인하려면 상세 페이지로 이동하세요.'}
        </p>
      </CardContent>
    </Card>
  );

  const renderPagination = () => {
    if (!data || totalPages <= 1) return null;
    return (
      <Pagination className="mt-4">
        <PaginationContent>
          <PaginationItem>
            <PaginationPrevious
              href="#"
              onClick={(event) => {
                event.preventDefault();
                setPage((prev) => Math.max(prev - 1, 0));
              }}
              className={page === 0 ? 'pointer-events-none opacity-50' : ''}
            />
          </PaginationItem>
          <PaginationItem>
            <div className="px-3 text-sm text-muted-foreground">
              {page + 1} / {totalPages}
            </div>
          </PaginationItem>
          <PaginationItem>
            <PaginationNext
              href="#"
              onClick={(event) => {
                event.preventDefault();
                setPage((prev) => (data && prev < totalPages - 1 ? prev + 1 : prev));
              }}
              className={page >= totalPages - 1 ? 'pointer-events-none opacity-50' : ''}
            />
          </PaginationItem>
        </PaginationContent>
      </Pagination>
    );
  };

  const handleCategoryChange = (event: React.ChangeEvent<HTMLSelectElement>) => {
    const value = event.target.value as 'all' | PostCategory;
    setCategory(value);
    setPage(0);
  };

  const postList = useMemo(() => data?.content ?? [], [data]);

  return (
    <div className="container mx-auto max-w-5xl px-4 py-10">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-3xl font-bold">커뮤니티</h1>
          <p className="text-sm text-muted-foreground">투자 전략과 아이디어를 공유하고 토론해보세요.</p>
        </div>
        <div className="flex items-center gap-2">
          {user ? (
            <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
              <DialogTrigger asChild>
                <Button className="rounded-full">
                  <PenSquare className="mr-2 h-4 w-4" />
                  새 게시글
                </Button>
              </DialogTrigger>
              <DialogContent className="max-w-2xl">
                <DialogHeader>
                  <DialogTitle>새 게시글 작성</DialogTitle>
                </DialogHeader>
                <form className="space-y-4" onSubmit={handleSubmit}>
                  <div className="space-y-2">
                    <Label htmlFor="title">제목</Label>
                    <Input id="title" placeholder="게시글 제목" {...form.register('title')} />
                    {form.formState.errors.title && (
                      <p className="text-xs text-destructive">{form.formState.errors.title.message}</p>
                    )}
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="category">카테고리</Label>
                    <select
                      id="category"
                      className="w-full rounded-md border border-border bg-background px-3 py-2 text-sm"
                      {...form.register('category')}
                    >
                      {categoryOptions
                        .filter((option) => option.value !== 'all')
                        .map((option) => (
                          <option key={option.value} value={option.value}>
                            {option.label}
                          </option>
                        ))}
                    </select>
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="contentType">작성 형식</Label>
                    <select
                      id="contentType"
                      className="w-full rounded-md border border-border bg-background px-3 py-2 text-sm"
                      {...form.register('contentType')}
                    >
                      {contentTypeOptions.map((option) => (
                        <option key={option.value} value={option.value}>
                          {option.label}
                        </option>
                      ))}
                    </select>
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="content">내용</Label>
                    <Textarea
                      id="content"
                      rows={8}
                      placeholder="게시글 내용을 작성하세요. Markdown을 지원합니다."
                      {...form.register('content')}
                    />
                    {form.formState.errors.content && (
                      <p className="text-xs text-destructive">{form.formState.errors.content.message}</p>
                    )}
                  </div>
                  <DialogFooter className="flex items-center gap-2">
                    <Button type="button" variant="outline" onClick={() => setDialogOpen(false)}>
                      취소
                    </Button>
                    <Button type="submit" disabled={isSubmitting}>
                      {isSubmitting && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                      등록
                    </Button>
                  </DialogFooter>
                </form>
              </DialogContent>
            </Dialog>
          ) : (
            <Button
              variant="outline"
              className="rounded-full"
              onClick={() => toast.info('로그인 후 게시글을 작성할 수 있습니다.')}
            >
              로그인 필요
            </Button>
          )}
        </div>
      </div>

      <Separator className="my-6" />

      <form className="flex flex-col gap-4 rounded-lg border border-border/80 p-4 md:flex-row md:items-end" onSubmit={handleSearch}>
        <div className="flex flex-1 flex-col gap-2">
          <Label htmlFor="keyword">검색어</Label>
          <Input
            id="keyword"
            placeholder="제목 또는 내용 검색"
            value={keyword}
            onChange={(event) => setKeyword(event.target.value)}
          />
        </div>
        <div className="flex flex-col gap-2">
          <Label htmlFor="categoryFilter">카테고리</Label>
          <select
            id="categoryFilter"
            className="rounded-md border border-border bg-background px-3 py-2 text-sm"
            value={category}
            onChange={handleCategoryChange}
          >
            {categoryOptions.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </div>
        <div className="flex items-end gap-2">
          <Button type="submit" className="rounded-full">
            검색
          </Button>
        </div>
      </form>

      {error && (
        <Alert variant="destructive" className="mt-6">
          <AlertTitle>오류</AlertTitle>
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      <div className="mt-6 space-y-3">
        {loading && (
          <div className="flex items-center gap-2 text-muted-foreground">
            <Loader2 className="h-4 w-4 animate-spin" />
            <span className="text-sm">게시글을 불러오는 중입니다...</span>
          </div>
        )}
        {postList.map((post) => renderPostCard(post))}
        {!loading && postList.length === 0 && (
          <div className="rounded-lg border border-border/80 px-4 py-12 text-center text-sm text-muted-foreground">
            검색 조건에 해당하는 게시글이 없습니다.
          </div>
        )}
      </div>

      {renderPagination()}
    </div>
  );
};

export default CommunityPage;
