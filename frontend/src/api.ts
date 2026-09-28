export interface ProductSummary {
  product_id: string;
  name: string;
  garment_type: string;
  description: string;
  colors: string[];
  price: number;
  image_url: string;
  in_stock_sizes: string[];
}

export interface SizeStock {
  size: string;
  quantity: number;
}

export interface ProductDetail extends ProductSummary {
  search_tags: string[];
  sizes: SizeStock[];
}

export async function fetchProducts(): Promise<ProductSummary[]> {
  const res = await fetch("/api/products");
  if (!res.ok) throw new Error("Failed to load products");
  return res.json();
}

export async function fetchProduct(productId: string): Promise<ProductDetail> {
  const res = await fetch(`/api/products/${encodeURIComponent(productId)}`);
  if (!res.ok) throw new Error("Failed to load product");
  return res.json();
}

export interface AuthUser {
  id: number;
  first_name: string;
  last_name: string;
  email: string;
}

export interface AuthResponse {
  token: string;
  user: AuthUser;
}

async function parseAuthError(res: Response): Promise<never> {
  let detail = "Something went wrong. Please try again.";
  try {
    const body = await res.json();
    if (typeof body.detail === "string") detail = body.detail;
  } catch {
    // ignore non-JSON error bodies
  }
  throw new Error(detail);
}

export async function signup(fields: {
  first_name: string;
  last_name: string;
  email: string;
  password: string;
  confirm_password: string;
}): Promise<AuthResponse> {
  const res = await fetch("/api/auth/signup", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(fields),
  });
  if (!res.ok) return parseAuthError(res);
  return res.json();
}

export async function login(fields: { email: string; password: string }): Promise<AuthResponse> {
  const res = await fetch("/api/auth/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(fields),
  });
  if (!res.ok) return parseAuthError(res);
  return res.json();
}

export async function fetchMe(token: string): Promise<AuthUser> {
  const res = await fetch("/api/auth/me", {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) throw new Error("Not authenticated");
  return res.json();
}

export async function logout(token: string): Promise<void> {
  await fetch("/api/auth/logout", {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
  });
}

export interface ChatProductCard {
  product_id: string;
  name: string;
  garment_type: string;
  price: number;
  image_url: string;
  description: string;
  in_stock_sizes: string[];
}

export interface ChatReply {
  reply: string;
  products: ChatProductCard[];
  search_query: string | null;
}

export interface PageContext {
  path: string;
  product_id: string | null;
}

export interface ChatHistoryMessage {
  role: "user" | "assistant";
  content: string;
  products: ChatProductCard[];
}

export async function sendChatMessage(
  message: string,
  page: PageContext,
  token: string | null,
): Promise<ChatReply> {
  const headers: Record<string, string> = { "Content-Type": "application/json" };
  if (token) headers.Authorization = `Bearer ${token}`;
  const res = await fetch("/api/chat", {
    method: "POST",
    headers,
    body: JSON.stringify({ message, page }),
  });
  if (!res.ok) throw new Error("Failed to reach the chat assistant");
  return res.json();
}

export async function fetchChatHistory(token: string): Promise<ChatHistoryMessage[]> {
  const res = await fetch("/api/chat/history", {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) throw new Error("Failed to load chat history");
  return res.json();
}
