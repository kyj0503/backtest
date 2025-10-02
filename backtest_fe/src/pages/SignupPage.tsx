import React, { useEffect } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
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

const signupSchema = z
  .object({
    username: z.string().min(2, '닉네임은 2자 이상 입력해주세요.').max(32, '닉네임은 최대 32자까지 입력할 수 있습니다.'),
    email: z.string().email('올바른 이메일 형식이 아닙니다.'),
    password: z.string().min(6, '비밀번호는 6자 이상 입력해주세요.'),
    confirmPassword: z.string().min(6, '비밀번호 확인을 입력해주세요.'),
    investmentType: z
      .enum(['conservative', 'moderate', 'balanced', 'aggressive', 'speculative']),
  })
  .refine((data) => data.password === data.confirmPassword, {
    message: '비밀번호가 일치하지 않습니다.',
    path: ['confirmPassword'],
  });

type SignupFormValues = z.infer<typeof signupSchema>;

const investmentLabels: Record<string, string> = {
  conservative: '안정형',
  moderate: '중립형',
  balanced: '균형형',
  aggressive: '적극형',
  speculative: '공격형',
};

const SignupPage: React.FC = () => {
  const { user, isLoading, register: registerUser } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const form = useForm<SignupFormValues>({
    resolver: zodResolver(signupSchema),
    defaultValues: {
      username: '',
      email: '',
      password: '',
      confirmPassword: '',
      investmentType: 'balanced',
    },
  });

  useEffect(() => {
    if (!isLoading && user) {
      const redirectTo = (location.state as { from?: string } | null)?.from ?? '/';
      navigate(redirectTo, { replace: true });
    }
  }, [isLoading, location.state, navigate, user]);

  const handleSubmit = form.handleSubmit(async (values) => {
    try {
      await registerUser({
        username: values.username,
        email: values.email,
        password: values.password,
        investmentType: values.investmentType,
      });
      toast.success('회원가입이 완료되었습니다. 환영합니다!');
      const redirectTo = (location.state as { from?: string } | null)?.from ?? '/';
      navigate(redirectTo, { replace: true });
    } catch (err) {
      const message = err instanceof Error ? err.message : '회원가입 중 오류가 발생했습니다.';
      toast.error(message);
    }
  });

  return (
    <div className="container mx-auto flex max-w-md justify-center px-4 py-16">
      <Card className="w-full shadow-md">
        <CardHeader>
          <CardTitle>회원가입</CardTitle>
          <CardDescription>기본 정보를 입력하여 커뮤니티와 채팅에 참여하세요.</CardDescription>
        </CardHeader>
        <form onSubmit={handleSubmit}>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="username">닉네임</Label>
              <Input id="username" placeholder="닉네임" {...form.register('username')} />
              {form.formState.errors.username && (
                <p className="text-xs text-destructive">{form.formState.errors.username.message}</p>
              )}
            </div>
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
            <div className="space-y-2">
              <Label htmlFor="confirmPassword">비밀번호 확인</Label>
              <Input
                id="confirmPassword"
                type="password"
                placeholder="********"
                {...form.register('confirmPassword')}
              />
              {form.formState.errors.confirmPassword && (
                <p className="text-xs text-destructive">{form.formState.errors.confirmPassword.message}</p>
              )}
            </div>
            <div className="space-y-2">
              <Label htmlFor="investmentType">투자 성향</Label>
              <select
                id="investmentType"
                className="rounded-md border border-border bg-background px-3 py-2 text-sm"
                {...form.register('investmentType')}
              >
                {Object.entries(investmentLabels).map(([value, label]) => (
                  <option key={value} value={value}>
                    {label}
                  </option>
                ))}
              </select>
            </div>
          </CardContent>
          <CardFooter className="flex flex-col gap-4">
            <Button type="submit" className="w-full" disabled={form.formState.isSubmitting}>
              {form.formState.isSubmitting && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              회원가입
            </Button>
            <p className="text-center text-sm text-muted-foreground">
              이미 계정이 있나요?{' '}
              <Link to="/login" className="text-primary hover:underline">
                로그인
              </Link>
            </p>
          </CardFooter>
        </form>
      </Card>
    </div>
  );
};

export default SignupPage;
