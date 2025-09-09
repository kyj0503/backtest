import React, { useState } from 'react';
import { login } from '../services/auth';

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
      <h2 className="text-2xl font-bold mb-6">로그인</h2>
      {done ? (
        <div className="p-4 bg-green-50 border border-green-200 rounded">로그인되었습니다. 상단 메뉴로 이동하세요.</div>
      ) : (
        <form onSubmit={onSubmit} className="space-y-4">
          {error && <div className="p-3 bg-red-50 border border-red-200 text-red-700 rounded">{error}</div>}
          <input className="w-full px-3 py-2 border rounded" type="email" placeholder="이메일" value={email} onChange={e => setEmail(e.target.value)} />
          <input className="w-full px-3 py-2 border rounded" type="password" placeholder="비밀번호" value={password} onChange={e => setPassword(e.target.value)} />
          <button className="w-full bg-blue-600 text-white rounded py-2">로그인</button>
        </form>
      )}
    </div>
  );
};

export default LoginPage;

