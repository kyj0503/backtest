export interface AuthUser {
  id: number;
  username: string;
  email: string;
  profileImage?: string;
  investmentType?: string;
  emailVerified?: boolean;
}
