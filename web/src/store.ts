import { createSignal } from "solid-js";
import { api, getToken, setToken, type User } from "./api";

const [user, setUser] = createSignal<User | null>(null);

export { user };

export async function loadMe(): Promise<User | null> {
  if (!getToken()) return null;
  try {
    const data = await api.me();
    setUser(data.user);
    return data.user;
  } catch {
    setToken(null);
    setUser(null);
    return null;
  }
}

export async function login(email: string, password: string): Promise<User> {
  const data = await api.login({ email, password });
  setToken(data.token);
  setUser(data.user);
  return data.user;
}

export async function register(email: string, password: string, displayName: string): Promise<User> {
  const data = await api.register({ email, password, display_name: displayName });
  setToken(data.token);
  setUser(data.user);
  return data.user;
}

export async function logout(): Promise<void> {
  try {
    await api.logout();
  } finally {
    setToken(null);
    setUser(null);
  }
}
