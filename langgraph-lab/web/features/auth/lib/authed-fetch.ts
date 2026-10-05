import { refreshApi } from "./auth-api";
import { useAuthStore } from "../store/auth-store";
import type { TokenPair } from "../types";

const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE ?? "http://127.0.0.1:8000";

/** تجديد واحد مشترك: طلبات متوازية تنتظر نفس الوعد بدل تجديد متكرر. */
let inflightRefresh: Promise<TokenPair> | null = null;

function refreshOnce(): Promise<TokenPair> {
  if (!inflightRefresh) {
    const refreshToken = useAuthStore.getState().refreshToken;
    if (!refreshToken) {
      return Promise.reject(new Error("يلزم تسجيل الدخول."));
    }
    inflightRefresh = refreshApi(refreshToken).finally(() => {
      inflightRefresh = null;
    });
  }
  return inflightRefresh;
}

/** جلب موثق: 401 ← تجديد صامت واحد ← إعادة الطلب مرة واحدة. */
export async function authedFetch(
  path: string,
  init?: RequestInit,
): Promise<Response> {
  const send = (token: string) =>
    fetch(`${API_BASE}${path}`, {
      ...init,
      headers: { ...init?.headers, Authorization: `Bearer ${token}` },
    });
  const accessToken = useAuthStore.getState().accessToken;
  if (!accessToken) throw new Error("يلزم تسجيل الدخول.");
  const first = await send(accessToken);
  if (first.status !== 401) return first;
  let tokens: TokenPair;
  try {
    tokens = await refreshOnce();
  } catch {
    useAuthStore.getState().clear();
    throw new Error("انتهت الجلسة، سجل الدخول مجددًا.");
  }
  useAuthStore.getState().setTokens(tokens);
  return send(tokens.access_token);
}
