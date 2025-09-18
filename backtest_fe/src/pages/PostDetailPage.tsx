import React from 'react';
import { useParams } from 'react-router-dom';

const PostDetailPage: React.FC = () => {
  const { id } = useParams();
  return (
    <div className="container mx-auto max-w-3xl px-4 py-10">
      <h1 className="text-2xl font-semibold">게시글 상세 (비활성화됨)</h1>
      <p className="mt-4 text-muted-foreground">게시글 조회 기능은 현재 비활성화되어 있습니다. (id: {id})</p>
    </div>
  );
};

export default PostDetailPage;
