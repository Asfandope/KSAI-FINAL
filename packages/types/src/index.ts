// User types
export type UserRole = 'user' | 'admin';

export interface User {
  id: string;
  email?: string | null;
  phoneNumber?: string | null;
  role: UserRole;
  createdAt: string;
  updatedAt: string;
}

// Content types
export type ContentType = 'pdf' | 'youtube';
export type ContentStatus = 'pending' | 'processing' | 'completed' | 'failed';
export type Language = 'en' | 'ta';
export type Category = 'Politics' | 'Environmentalism' | 'SKCRF' | 'Educational Trust' | string;

export interface Content {
  id: string;
  title: string;
  sourceUrl: string;
  sourceType: ContentType;
  language: Language;
  category: Category;
  needsTranslation: boolean;
  status: ContentStatus;
  createdAt: string;
  updatedAt: string;
}

// Conversation types
export type MessageSender = 'user' | 'ai';

export interface Message {
  id: string;
  conversationId: string;
  sender: MessageSender;
  textContent: string;
  imageUrl?: string | null;
  videoUrl?: string | null;
  videoTimestamp?: number | null;
  createdAt: string;
}

export interface Conversation {
  id: string;
  userId: string;
  topic: Category;
  createdAt: string;
  updatedAt: string;
  messages: Message[];
}

// API request/response types
export interface RegisterRequest {
  email?: string | null;
  phoneNumber?: string | null;
  password: string;
}

export interface LoginRequest {
  username: string;
  password: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
}

export interface ChatRequest {
  query: string;
  language: Language;
  topic: Category;
  conversationId?: string | null;
}

export interface ApiError {
  detail: string;
}

// UI component types
export interface ButtonProps {
  variant?: 'primary' | 'secondary' | 'outline' | 'ghost' | 'destructive';
  size?: 'sm' | 'md' | 'lg';
  disabled?: boolean;
  loading?: boolean;
  children: React.ReactNode;
  onClick?: () => void;
  type?: 'button' | 'submit' | 'reset';
  className?: string;
}

export interface InputProps {
  label?: string;
  placeholder?: string;
  value?: string;
  onChange?: (value: string) => void;
  type?: 'text' | 'email' | 'password' | 'tel';
  required?: boolean;
  disabled?: boolean;
  error?: string;
  className?: string;
}

export interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  title?: string;
  children: React.ReactNode;
  size?: 'sm' | 'md' | 'lg' | 'xl';
}

// Chat UI types
export interface ChatMessageProps {
  message: Message;
  isUser?: boolean;
}

export interface ChatInputProps {
  onSend: (message: string) => void;
  disabled?: boolean;
  placeholder?: string;
  supportVoice?: boolean;
}

// Admin types
export interface AdminDashboardStats {
  totalContent: number;
  pendingContent: number;
  totalUsers: number;
  activeConversations: number;
}

export interface UploadContentRequest {
  file?: File | null;
  youtubeUrl?: string | null;
  category: string;
  language: Language;
  needsTranslation: boolean;
}

export interface UploadResponse {
  message: string;
  contentId: string;
}