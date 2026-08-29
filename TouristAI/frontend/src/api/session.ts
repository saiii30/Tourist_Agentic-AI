const SESSION_KEY = "touristai.chat_session_id";
const TOKEN_KEY = "touristai.access_token";
const TOKEN_EXPIRY_KEY = "touristai.access_token_expires_at";


export const getChatSessionId = (): string => {
  const existing = localStorage.getItem(SESSION_KEY);
  if (existing) return existing;
  const id = `web:${crypto.randomUUID()}`;
  localStorage.setItem(SESSION_KEY, id);
  return id;
};


export const resetChatSessionId = (): string => {
  localStorage.removeItem(SESSION_KEY);
  return getChatSessionId();
};


export const getAccessToken = (): string | null => {
  const token = localStorage.getItem(TOKEN_KEY);
  const expiresAt = localStorage.getItem(TOKEN_EXPIRY_KEY);
  if (token && expiresAt && Date.parse(expiresAt) <= Date.now()) {
    setAccessToken(null);
    return null;
  }
  return token;
};

export const setAccessToken = (token: string | null, expiresAt?: string): void => {
  if (token) {
    localStorage.setItem(TOKEN_KEY, token);
    if (expiresAt) localStorage.setItem(TOKEN_EXPIRY_KEY, expiresAt);
  } else {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(TOKEN_EXPIRY_KEY);
  }
};

export const authHeaders = (): Record<string, string> => {
  const token = getAccessToken();
  return token ? { Authorization: `Bearer ${token}` } : {};
};
