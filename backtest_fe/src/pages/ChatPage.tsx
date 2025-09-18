import React from 'react';

const ChatPage: React.FC = () => {
  return (
    <div className="container mx-auto px-4 py-10 max-w-3xl">
      <h2 className="text-xl font-semibold">채팅 (비활성화됨)</h2>
      <p className="mt-4 text-muted-foreground">현재 채팅 기능은 비활성화되어 있습니다.</p>
    </div>
  );
};

export default ChatPage;

