import React, { useState } from 'react';
import { register } from '../services/auth';
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";

const SignupPage: React.FC = () => {
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [done, setDone] = useState(false);

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    try {
      await register({ username, email, password });
      setDone(true);
    } catch (err: any) {
      setError(err?.message || '회원가입에 실패했습니다.');
    }
  };

  return (
    <div className="container mx-auto px-4 max-w-md py-10">
      <Card>
        <CardHeader>
          <CardTitle>회원가입</CardTitle>
        </CardHeader>
        <CardContent>
          {done ? (
            <div className="p-4 bg-green-50 border border-green-200 rounded text-green-800">
              가입이 완료되었습니다. 로그인 해 주세요.
            </div>
          ) : (
            <form onSubmit={onSubmit} className="space-y-4">
              {error && (
                <div className="p-3 bg-red-50 border border-red-200 text-red-700 rounded">
                  {error}
                </div>
              )}
              <div className="space-y-2">
                <Label htmlFor="username">사용자명</Label>
                <Input 
                  id="username"
                  placeholder="사용자명을 입력하세요" 
                  value={username} 
                  onChange={e => setUsername(e.target.value)} 
                />
              </div>
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
                  placeholder="비밀번호(8자 이상)를 입력하세요" 
                  value={password} 
                  onChange={e => setPassword(e.target.value)} 
                />
              </div>
              <Button type="submit" className="w-full">
                가입하기
              </Button>
            </form>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

export default SignupPage;

