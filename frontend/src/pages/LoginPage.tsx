import React, { useState } from 'react';
import { login } from '../services/auth';
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";

const LoginPage: React.FC = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [done, setDone] = useState(false);

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    try {
      await login({ email, password });
      setDone(true);
    } catch (err: any) {
      setError(err?.message || '로그인에 실패했습니다.');
    }
  };

  return (
    <div className="container mx-auto px-4 max-w-md py-10">
      <Card>
        <CardHeader>
          <CardTitle>로그인</CardTitle>
        </CardHeader>
        <CardContent>
          {done ? (
            <div className="p-4 bg-green-50 border border-green-200 rounded text-green-800">
              로그인되었습니다. 상단 메뉴로 이동하세요.
            </div>
          ) : (
            <form onSubmit={onSubmit} className="space-y-4">
              {error && (
                <div className="p-3 bg-red-50 border border-red-200 text-red-700 rounded">
                  {error}
                </div>
              )}
              <div className="space-y-2">
                <Label htmlFor="email">이메일</Label>
                <Input 
                  id="email"
                  type="email" 
                  placeholder="이메일을 입력하세요" 
                  value={email} 
                  onChange={e => setEmail(e.target.value)} 
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="password">비밀번호</Label>
                <Input 
                  id="password"
                  type="password" 
                  placeholder="비밀번호를 입력하세요" 
                  value={password} 
                  onChange={e => setPassword(e.target.value)} 
                />
              </div>
              <Button type="submit" className="w-full">
                로그인
              </Button>
            </form>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

export default LoginPage;

