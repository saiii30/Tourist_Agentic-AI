import axios from "axios";
import { apiUrl } from "./config";
import { authHeaders, resetChatSessionId, setAccessToken } from "./session";


export const register = async (email: string, password: string, displayName: string) => {
  const { data } = await axios.post(apiUrl("/api/auth/register"), { email, password, display_name: displayName });
  setAccessToken(data.access_token, data.expires_at);
  resetChatSessionId();
  return data;
};

export const login = async (email: string, password: string) => {
  const { data } = await axios.post(apiUrl("/api/auth/login"), { email, password });
  setAccessToken(data.access_token, data.expires_at);
  resetChatSessionId();
  return data;
};

export const currentUser = async () => {
  const { data } = await axios.get(apiUrl("/api/auth/me"), { headers: authHeaders() });
  return data.user;
};

export const logout = async () => {
  try {
    await axios.post(apiUrl("/api/auth/logout"), {}, { headers: authHeaders() });
  } finally {
    setAccessToken(null);
    resetChatSessionId();
  }
};
