import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { useAuth } from '@/features/auth/hooks/useAuth';
import {
  ChatMessage,
  ChatRoom,
  fetchChatRooms,
  fetchRecentMessages,
  joinRoom,
  leaveRoom,
  sendMessage,
} from '@/features/chat/services/chat';
import { buildWebSocketUrl } from '@/shared/api/ws';
import { SimpleStompClient } from '@/features/chat/lib/simple-stomp';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/shared/ui/card';
import { Button } from '@/shared/ui/button';
import { Badge } from '@/shared/ui/badge';
import { ScrollArea } from '@/shared/ui/scroll-area';
import { Textarea } from '@/shared/ui/textarea';
import { Input } from '@/shared/ui/input';
import { Separator } from '@/shared/ui/separator';
import { toast } from 'sonner';
import { Loader2, MessageSquarePlus, Send } from 'lucide-react';
import { cn } from '@/shared/lib/core/utils';
import { formatRelative } from 'date-fns';

const ChatPage: React.FC = () => {
  const { user, isLoading: authLoading } = useAuth();
  const [rooms, setRooms] = useState<ChatRoom[]>([]);
  const [roomsLoading, setRoomsLoading] = useState(true);
  const [roomsError, setRoomsError] = useState<string | null>(null);
  const [selectedRoom, setSelectedRoom] = useState<ChatRoom | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [messageInput, setMessageInput] = useState('');
  const [joining, setJoining] = useState(false);
  const [memberJoined, setMemberJoined] = useState(false);
  const [, setSubscriptionId] = useState<string | null>(null);
  const wsClientRef = useRef<SimpleStompClient | null>(null);
  const [wsConnected, setWsConnected] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement | null>(null);

  // Helper to suppress noisy connection-related toasts
  const showChatError = (message: string) => {
    try {
      const m = (message || '').toString();
      // suppress backend connection-like messages that are noisy on navigation
      if (/수신|채널|연결하지 못했습니다|채널에 연결/i.test(m)) {
        console.warn('Suppressed chat error toast:', m);
        return;
      }
    } catch (e) {
      // ignore
    }
    toast.error(message);
  };

  const scrollToBottom = useCallback(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, scrollToBottom]);

  useEffect(() => {
    const loadRooms = async () => {
      setRoomsLoading(true);
      setRoomsError(null);
      try {
        const response = await fetchChatRooms({ size: 50 });
        setRooms(response.content);
        if (response.content.length > 0) {
          setSelectedRoom((prev) => prev ?? response.content[0]);
        }
      } catch (err) {
        const message = err instanceof Error ? err.message : '채팅방을 불러오는 중 오류가 발생했습니다.';
        setRoomsError(message);
      } finally {
        setRoomsLoading(false);
      }
    };

    void loadRooms();
  }, []);

  // Auto-join when the initial selectedRoom is set and user is logged in
  useEffect(() => {
    const tryAutoJoin = async () => {
      if (!selectedRoom) return;
      if (!user) return;
      // if already marked as joined, do nothing
      if (memberJoined) return;
      try {
        setJoining(true);
        await joinRoom(selectedRoom.id);
        setMemberJoined(true);
      } catch (error) {
        const message = error instanceof Error ? error.message : '자동 참여 중 오류가 발생했습니다.';
        if (message.includes('이미') || message.toLowerCase().includes('already')) {
          setMemberJoined(true);
        } else {
          // don't spam the user on initial load; show info only
          console.warn('자동 채팅방 참여 실패:', message);
        }
      } finally {
        setJoining(false);
      }
    };

    void tryAutoJoin();
  }, [selectedRoom, user]);

  useEffect(() => {
    const url = buildWebSocketUrl();
    const client = new SimpleStompClient(url);
    wsClientRef.current = client;
    let mounted = true;
    void (async () => {
      // Show a connecting toast only if connect takes longer than a short threshold
      const CONNECT_TOAST_DELAY = 800; // ms
      let toastTimer: number | null = null;
      let toastId: string | number | null = null;
      try {
        toastTimer = window.setTimeout(() => {
          // Do not show a toast here; rely on header badge for connection status.
          console.debug('Chat connect taking longer than threshold; showing status badge.');
        }, CONNECT_TOAST_DELAY);

        await client.connect();
        if (!mounted) return;
        // connected quickly -> cancel pending toast (if any)
        if (toastTimer) {
          clearTimeout(toastTimer);
          toastTimer = null;
        }
        if (toastId) {
          try { /* sonner auto-dismiss handles duration; optionally dismiss manually if supported */ } catch (_) {}
          toastId = null;
        }
        setWsConnected(true);
      } catch (error) {
        console.warn('웹소켓 연결 실패 (무시)', error);
        if (!mounted) return;
        if (toastTimer) {
          clearTimeout(toastTimer);
          toastTimer = null;
        }
        // If a connecting toast was shown, replace it with a non-blocking status via UI (we already show '오프라인' badge)
        setWsConnected(false);
      }
    })();
    return () => {
      mounted = false;
      // 연결 상태를 확인한 후 안전하게 연결 해제
      try { 
        if (client.isConnected()) {
          client.disconnect(); 
        }
      } catch (error) {
        console.debug('WebSocket disconnect error (ignored):', error);
      }
      wsClientRef.current = null;
    };
  }, []);

  useEffect(() => {
    const client = wsClientRef.current;
    if (!client || !wsConnected) return;
    if (!selectedRoom) return;

    const destination = `/topic/chatrooms/${selectedRoom.id}`;
    const unsubscribe = client.subscribe(destination, (frame) => {
      try {
        const payload = JSON.parse(frame.body) as ChatMessage;
        setMessages((prev) => {
          const exists = prev.some((message) => message.id === payload.id);
          if (exists) return prev;
          return [...prev, payload].sort((a, b) => a.createdAt.localeCompare(b.createdAt));
        });
      } catch (error) {
        console.error('메시지 파싱 실패', error);
      }
    });
    setSubscriptionId(destination);

    return () => {
      unsubscribe();
      setSubscriptionId(null);
    };
  }, [selectedRoom, wsConnected]);

  useEffect(() => {
    const loadMessages = async () => {
      if (!selectedRoom) {
        setMessages([]);
        return;
      }
      try {
        const recent = await fetchRecentMessages(selectedRoom.id);
        const sorted = [...recent].sort((a, b) => a.createdAt.localeCompare(b.createdAt));
        setMessages(sorted);
        } catch (error) {
        const message = error instanceof Error ? error.message : '메시지를 불러오는 중 오류가 발생했습니다.';
        showChatError(message);
        setMessages([]);
      }
    };

    void loadMessages();
  }, [selectedRoom]);

  const handleSelectRoom = async (room: ChatRoom) => {
    if (selectedRoom?.id === room.id) return;
    setSelectedRoom(room);
    setMemberJoined(false);
    if (!user) {
      toast.info('로그인 후 채팅방에 참여하여 메시지를 보낼 수 있습니다.');
      return;
    }
    try {
      setJoining(true);
      await joinRoom(room.id);
      setMemberJoined(true);
      } catch (error) {
      const message = error instanceof Error ? error.message : '채팅방 참여 중 오류가 발생했습니다.';
      if (message.includes('이미') || message.toLowerCase().includes('already')) {
        setMemberJoined(true);
      } else {
        showChatError(message);
      }
    } finally {
      setJoining(false);
    }
  };

  const handleSendMessage = async () => {
    if (!selectedRoom) return;
    if (!user) {
      toast.error('로그인 후 메시지를 보낼 수 있습니다.');
      return;
    }
    if (!memberJoined) {
      toast.info('채팅방에 참여 중인지 확인해주세요. 자동으로 다시 시도합니다.');
      try {
        await joinRoom(selectedRoom.id);
        setMemberJoined(true);
      } catch (error) {
        const message = error instanceof Error ? error.message : '채팅방에 참여할 수 없습니다.';
        toast.error(message);
        return;
      }
    }
    if (!messageInput.trim()) return;

    const content = messageInput.trim();
    setMessageInput('');
    try {
      const response = await sendMessage(selectedRoom.id, { content });
      setMessages((prev) => {
        const exists = prev.some((message) => message.id === response.id);
        if (exists) return prev;
        return [...prev, response].sort((a, b) => a.createdAt.localeCompare(b.createdAt));
      });
      } catch (error) {
        const message = error instanceof Error ? error.message : '메시지를 전송하지 못했습니다.';
        showChatError(message);
      setMessageInput(content);
    }
  };

  const handleLeaveRoom = async () => {
    if (!selectedRoom) return;
    try {
      await leaveRoom(selectedRoom.id);
      setMemberJoined(false);
      toast.success('채팅방에서 나갔습니다.');
    } catch (error) {
      const message = error instanceof Error ? error.message : '채팅방 나가기 중 오류가 발생했습니다.';
      showChatError(message);
    }
  };

  const renderRoom = (room: ChatRoom) => {
    const active = selectedRoom?.id === room.id;
    return (
      <Card
        key={room.id}
        className={cn(
          'shadow-sm transition hover:border-primary/60 hover:shadow-md',
          active ? 'border-primary' : 'border-border'
        )}
      >
        <CardHeader className="flex flex-row items-start justify-between space-y-0">
          <div>
            <CardTitle className="text-base font-semibold">{room.name}</CardTitle>
            <CardDescription className="line-clamp-2 text-xs">{room.description || '설명이 없습니다.'}</CardDescription>
          </div>
          <Badge variant={room.active ? 'secondary' : 'outline'} className="rounded-full text-[10px] uppercase">
            {room.active ? 'Active' : 'Inactive'}
          </Badge>
        </CardHeader>
        <CardContent className="flex items-center justify-between gap-3">
          <div className="flex flex-col text-xs text-muted-foreground">
            <span>유형: {room.roomType}</span>
            <span>
              인원: {room.currentMembers ?? 0}
              {room.maxMembers ? ` / ${room.maxMembers}` : ''}
            </span>
          </div>
          <Button size="sm" variant={active ? 'secondary' : 'outline'} onClick={() => void handleSelectRoom(room)}>
            {active ? '선택됨' : '입장'}
          </Button>
        </CardContent>
      </Card>
    );
  };

  const selectedRoomHeader = useMemo(() => {
    if (!selectedRoom) {
      return (
        <div className="flex h-full flex-col items-center justify-center text-muted-foreground">
          <MessageSquarePlus className="mb-2 h-10 w-10" />
          <p className="text-sm">참여할 채팅방을 선택해주세요.</p>
        </div>
      );
    }

    return (
      <div className="flex flex-col gap-1">
        <div className="flex items-center gap-2">
          <h2 className="text-xl font-semibold text-foreground">{selectedRoom.name}</h2>
          <Badge variant="outline" className="rounded-full capitalize">
            {selectedRoom.roomType}
          </Badge>
          <div className="ml-2">
            <Badge variant={wsConnected ? 'secondary' : 'outline'} className="rounded-full text-xs">
              {wsConnected ? '연결됨' : '오프라인'}
            </Badge>
          </div>
        </div>
        <p className="text-sm text-muted-foreground">{selectedRoom.description || '설명이 없습니다.'}</p>
        <div className="flex items-center gap-3 text-xs text-muted-foreground">
          <span>인원 {selectedRoom.currentMembers ?? 0}</span>
          {selectedRoom.maxMembers && <span>최대 {selectedRoom.maxMembers}</span>}
          <span>생성자 {selectedRoom.creator.username}</span>
        </div>
      </div>
    );
  }, [selectedRoom]);

  const canSendMessage = Boolean(user && selectedRoom && memberJoined);

  return (
    <div className="container mx-auto grid max-w-6xl gap-6 px-4 py-10 md:grid-cols-[320px,1fr]">
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-semibold">실시간 채팅</h1>
          {roomsLoading && <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />}
        </div>
        <Separator />
        {roomsError && <p className="text-sm text-destructive">{roomsError}</p>}
        <ScrollArea className="h-[calc(100vh-240px)] rounded-lg border border-border/80 p-2">
          <div className="space-y-3">
            {rooms.map((room) => renderRoom(room))}
            {!roomsLoading && rooms.length === 0 && (
              <div className="text-center text-sm text-muted-foreground">사용 가능한 채팅방이 없습니다.</div>
            )}
          </div>
        </ScrollArea>
      </div>

      <Card className="min-h-[520px] shadow-sm">
        <CardHeader className="flex flex-col sm:flex-row sm:items-center sm:justify-between">
          {selectedRoomHeader}
          {selectedRoom && user && (
            <div className="flex items-center gap-2">
              <Badge variant={memberJoined ? 'secondary' : 'outline'} className="rounded-full">
                {memberJoined ? '참여 중' : '참여 안 함'}
              </Badge>
              <Button variant="outline" size="sm" disabled={!memberJoined || joining} onClick={() => void handleLeaveRoom()}>
                나가기
              </Button>
            </div>
          )}
        </CardHeader>
        <CardContent className="flex h-full flex-col gap-4">
          <ScrollArea className="h-[400px] rounded-lg border border-border/70 p-3">
            <div className="space-y-3">
              {messages.map((message) => {
                const isOwn = user && message.senderId === user.id;
                return (
                  <div key={message.id} className={cn('flex flex-col gap-1 rounded-lg border px-3 py-2 shadow-sm', isOwn ? 'border-primary/70 bg-primary/5' : 'border-border/80 bg-background')}
                  >
                    <div className="flex items-center justify-between">
                      <span className={cn('text-sm font-semibold', isOwn ? 'text-primary' : 'text-foreground')}>
                        {message.senderName}
                      </span>
                      <span className="text-xs text-muted-foreground">
                        {formatRelative(new Date(message.createdAt), new Date())}
                      </span>
                    </div>
                    <p className="whitespace-pre-wrap text-sm text-foreground">{message.content}</p>
                  </div>
                );
              })}
              {messages.length === 0 && (
                <div className="py-12 text-center text-sm text-muted-foreground">메시지가 없습니다. 첫 메시지를 남겨보세요.</div>
              )}
              <div ref={messagesEndRef} />
            </div>
          </ScrollArea>

          <div className="space-y-3 rounded-lg border border-border/80 p-3">
            {!user && !authLoading && (
              <div className="rounded-md border border-dashed border-primary/50 bg-primary/5 px-3 py-2 text-sm text-primary">
                로그인 후 메시지를 보낼 수 있습니다.
              </div>
            )}
            {selectedRoom ? (
              <>
                <Textarea
                  value={messageInput}
                  onChange={(event) => setMessageInput(event.target.value)}
                  placeholder={memberJoined ? '메시지를 입력하세요...' : '채팅방에 참여하면 메시지를 보낼 수 있습니다.'}
                  rows={3}
                  disabled={!user || !memberJoined || joining}
                  className="resize-none"
                />
                <div className="flex items-center justify-between gap-3">
                  <Input
                    placeholder="메시지 종류 (기본: text)"
                    value="text"
                    disabled
                    className="max-w-[140px] text-xs"
                  />
                  <div className="flex items-center gap-2">
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => void handleLeaveRoom()}
                      disabled={!memberJoined}
                    >
                      나가기
                    </Button>
                    <Button
                      onClick={() => void handleSendMessage()}
                      disabled={!canSendMessage || joining || !messageInput.trim()}
                    >
                      {joining && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                      <Send className="mr-2 h-4 w-4" />
                      보내기
                    </Button>
                  </div>
                </div>
              </>
            ) : (
              <div className="rounded-md border border-dashed border-border px-3 py-6 text-center text-sm text-muted-foreground">
                채팅방을 먼저 선택해주세요.
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default ChatPage;
