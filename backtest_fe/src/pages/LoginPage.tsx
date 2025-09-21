import React, { useEffect } from 'react';
import { useNavigate, useLocation, Link } from 'react-router-dom';
import { useAuth } from '@/features/auth/hooks/useAuth';
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from '@/shared/ui/card';
import { Button } from '@/shared/ui/button';
import { Input } from '@/shared/ui/input';
import { Label } from '@/shared/ui/label';
import { useForm } from 'react-hook-form';
import { z } from 'zod';
import { zodResolver } from '@hookform/resolvers/zod';
import { toast } from 'sonner';
import { Loader2 } from 'lucide-react';

const loginSchema = z.object({
  email: z.string().email('올바른 이메일 형식이 아닙니다.'),
  password: z.string().min(6, '비밀번호는 6자 이상 입력해주세요.'),
});

type LoginFormValues = z.infer<typeof loginSchema>;

const LoginPage: React.FC = () => {
  const { user, login, isLoading } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const form = useForm<LoginFormValues>({
    resolver: zodResolver(loginSchema),
    defaultValues: { email: '', password: '' },
  });

  useEffect(() => {
    if (!isLoading && user) {
      const redirectTo = (location.state as { from?: string } | null)?.from ?? '/';
      navigate(redirectTo, { replace: true });
    }
  }, [isLoading, location.state, navigate, user]);

  const handleSubmit = form.handleSubmit(async (values) => {
    try {
      await login(values);
      toast.success('로그인에 성공했습니다.');
      const redirectTo = (location.state as { from?: string } | null)?.from ?? '/';
      navigate(redirectTo, { replace: true });
    } catch (err) {
      const message = err instanceof Error ? err.message : '로그인 중 오류가 발생했습니다.';
      toast.error(message);
    }
  });

  return (
    <div className="container mx-auto flex max-w-md justify-center px-4 py-16">
      <Card className="w-full shadow-md">
        <CardHeader>
          <CardTitle>로그인</CardTitle>
          <CardDescription>등록된 이메일과 비밀번호로 로그인하세요.</CardDescription>
        </CardHeader>
        <form onSubmit={handleSubmit}>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="email">이메일</Label>
              <Input id="email" type="email" placeholder="you@example.com" {...form.register('email')} />
              {form.formState.errors.email && (
                <p className="text-xs text-destructive">{form.formState.errors.email.message}</p>
              )}
            </div>
            <div className="space-y-2">
              <Label htmlFor="password">비밀번호</Label>
              <Input id="password" type="password" placeholder="********" {...form.register('password')} />
              {form.formState.errors.password && (
                <p className="text-xs text-destructive">{form.formState.errors.password.message}</p>
              )}
            </div>
          </CardContent>
          <CardFooter className="flex flex-col gap-4">
            <Button type="submit" className="w-full" disabled={form.formState.isSubmitting}>
              {form.formState.isSubmitting && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              로그인
            </Button>
            <p className="text-center text-sm text-muted-foreground">
              아직 계정이 없나요?{' '}
              <Link to="/signup" className="text-primary hover:underline">
                회원가입
              </Link>
            </p>
          </CardFooter>
        </form>
      </Card>
    </div>
  );
};

export default LoginPage;
