import { apiClient, extractErrorMessage } from '@/shared/api/client';

export type ChatRoomType = 'public' | 'private' | 'direct';
export type ChatMessageType = 'text' | 'image' | 'file' | 'system';

export interface ChatRoom {
  id: number;
  name: string;
  description: string | null;
  roomType: ChatRoomType;
  maxMembers: number | null;
  currentMembers: number | null;
  active: boolean;
  createdAt: string;
  updatedAt: string;
  creator: {
    id: number;
    username: string;
  };
}

export interface ChatMessage {
  id: number;
  roomId: number;
  senderId: number;
  senderName: string;
  messageType: ChatMessageType;
  content: string;
  fileUrl: string | null;
  fileName: string | null;
  fileSize: number | null;
  replyToId: number | null;
  deleted: boolean;
  createdAt: string;
  updatedAt: string;
}

export interface ChatRoomMember {
  id: number;
  userId: number;
  username: string;
  role: string;
  active: boolean;
  joinedAt: string;
  lastReadAt: string | null;
}

export interface PageResponse<T> {
  content: T[];
  totalElements: number;
  totalPages: number;
  number: number;
  size: number;
}

export interface ListChatRoomParams {
  page?: number;
  size?: number;
  type?: ChatRoomType;
}

export interface SendMessagePayload {
  content: string;
  messageType?: ChatMessageType;
  fileUrl?: string;
  fileName?: string;
  fileSize?: number;
  replyToId?: number;
}

export const fetchChatRooms = async (params: ListChatRoomParams = {}): Promise<PageResponse<ChatRoom>> => {
  const query: Record<string, string> = {
    page: String(params.page ?? 0),
    size: String(params.size ?? 20),
  };
  if (params.type) {
    query.type = params.type;
  }
  try {
    const { data } = await apiClient.get<PageResponse<ChatRoom>>('/v1/chat/rooms', {
      params: query,
    });
    return data;
  } catch (err) {
    throw new Error(extractErrorMessage(err));
  }
};

export const joinRoom = async (roomId: number): Promise<ChatRoomMember> => {
  try {
    const { data } = await apiClient.post<ChatRoomMember>(`/v1/chat/rooms/${roomId}/join`);
    return data;
  } catch (err) {
    throw new Error(extractErrorMessage(err));
  }
};

export const leaveRoom = async (roomId: number): Promise<void> => {
  try {
    await apiClient.post(`/v1/chat/rooms/${roomId}/leave`);
  } catch (err) {
    throw new Error(extractErrorMessage(err));
  }
};

export const fetchRecentMessages = async (roomId: number): Promise<ChatMessage[]> => {
  try {
    const { data } = await apiClient.get<ChatMessage[]>(`/v1/chat/rooms/${roomId}/messages/recent`);
    return data;
  } catch (err) {
    throw new Error(extractErrorMessage(err));
  }
};

export const fetchMessages = async (
  roomId: number,
  params: { page?: number; size?: number } = {}
): Promise<PageResponse<ChatMessage>> => {
  const query: Record<string, string> = {
    page: String(params.page ?? 0),
    size: String(params.size ?? 50),
  };
  try {
    const { data } = await apiClient.get<PageResponse<ChatMessage>>(`/v1/chat/rooms/${roomId}/messages`, {
      params: query,
    });
    return data;
  } catch (err) {
    throw new Error(extractErrorMessage(err));
  }
};

export const sendMessage = async (roomId: number, payload: SendMessagePayload): Promise<ChatMessage> => {
  try {
    const { data } = await apiClient.post<ChatMessage>(`/v1/chat/rooms/${roomId}/messages`, {
      messageType: payload.messageType ?? 'text',
      content: payload.content,
      fileUrl: payload.fileUrl ?? null,
      fileName: payload.fileName ?? null,
      fileSize: payload.fileSize ?? null,
      replyToId: payload.replyToId ?? null,
    });
    return data;
  } catch (err) {
    throw new Error(extractErrorMessage(err));
  }
};
