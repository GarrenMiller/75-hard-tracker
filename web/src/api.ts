export interface User {
  id: number;
  email: string;
  display_name: string;
  created_at?: string;
}

export interface GoalType {
  key: string;
  name: string;
  description: string;
  period: string;
  config_schema: {
    properties: Record<string, { type: string; title?: string }>;
    required: string[];
  };
}

export interface Goal {
  id: number;
  name: string;
  goal_type_key: string;
  goal_type_name: string;
  period: string;
  config: Record<string, unknown>;
  active: boolean;
  created_at: string;
  today?: {
    completed: boolean;
    progress: number;
    detail: Record<string, unknown>;
  };
}

export interface CheckIn {
  id: number;
  goal_id: number;
  plan_id: number | null;
  completed_at: string;
  value: Record<string, unknown>;
}

export interface Plan {
  id: number;
  name: string;
  difficulty_rules: {
    duration_days: number;
    lapse_policy: "restart_on_fail" | "grace_days";
    grace_days: number;
  };
  started_at: string;
  status: string;
  cycle_count: number;
  goal_count: number;
  cycle_day: number | null;
  cycle_total_days: number | null;
  goals?: Goal[];
}

export interface Progress {
  plan: Plan;
  cycle: {
    id: number;
    started_at: string;
    day: number;
    total_days: number;
    missed_days: number;
  } | null;
  days: {
    date: string;
    status: string;
    goals: {
      id: number;
      name: string;
      goal_type_key: string;
      completed: boolean;
      progress: number;
      detail: Record<string, unknown>;
    }[];
  }[];
  goals: {
    goal: Goal;
    today: { completed: boolean; progress: number; detail: Record<string, unknown> };
    streak: number;
  }[];
}

export interface Profile {
  user: User;
  stats: {
    goals_total: number;
    goals_active: number;
    plans_total: number;
    plans_active: number;
    plans_failed: number;
    check_ins_total: number;
    best_streak: number;
    member_days: number;
  };
  goals: {
    goal: Goal;
    streak: number;
    total_completions: number;
    last_completed_at: string | null;
    plans: { id: number; name: string }[];
  }[];
  plans: {
    plan: Plan;
    cycle_day: number | null;
    cycle_total_days: number | null;
  }[];
}

const API_BASE = "/api";

let token: string | null = localStorage.getItem("token");

export function setToken(t: string | null) {
  token = t;
  if (t) localStorage.setItem("token", t);
  else localStorage.removeItem("token");
}

export function getToken(): string | null {
  return token;
}

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string> | undefined),
  };
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const res = await fetch(`${API_BASE}${path}`, { ...options, headers });
  if (!res.ok) {
    let message = `Request failed (${res.status})`;
    try {
      const data = await res.json();
      if (data.error) message = data.error;
    } catch {
      /* ignore */
    }
    throw new ApiError(res.status, message);
  }
  return res.json() as Promise<T>;
}

export const api = {
  register: (body: { email: string; password: string; display_name: string }) =>
    request<{ token: string; user: User }>("/auth/register", { method: "POST", body: JSON.stringify(body) }),

  login: (body: { email: string; password: string }) =>
    request<{ token: string; user: User }>("/auth/login", { method: "POST", body: JSON.stringify(body) }),

  logout: () => request<{ ok: boolean }>("/auth/logout", { method: "POST" }),

  me: () => request<{ user: User }>("/auth/me"),

  goalTypes: () => request<{ goal_types: GoalType[] }>("/goal-types"),

  createGoal: (body: { name: string; goal_type_key: string; config: Record<string, unknown> }) =>
    request<Goal>("/goals", { method: "POST", body: JSON.stringify(body) }),

  listGoals: () => request<{ goals: Goal[] }>("/goals"),

  updateGoal: (id: number, body: Partial<{ name: string; config: Record<string, unknown>; active: boolean }>) =>
    request<Goal>(`/goals/${id}`, { method: "PATCH", body: JSON.stringify(body) }),

  deleteGoal: (id: number) => request<{ ok: boolean }>(`/goals/${id}`, { method: "DELETE" }),

  createCheckIn: (goalId: number, body: { value?: Record<string, unknown>; completed_at?: string }) =>
    request<CheckIn>(`/goals/${goalId}/check-ins`, { method: "POST", body: JSON.stringify(body) }),

  listCheckIns: (goalId: number) => request<{ check_ins: CheckIn[] }>(`/goals/${goalId}/check-ins`),

  createPlan: (body: {
    name: string;
    goal_ids: number[];
    difficulty_rules: Record<string, unknown>;
  }) =>
    request<Plan>("/plans", { method: "POST", body: JSON.stringify(body) }),

  listPlans: () => request<{ plans: Plan[] }>("/plans"),

  getPlan: (id: number) => request<Plan>(`/plans/${id}`),

  updatePlan: (id: number, body: Partial<{ name: string; goal_ids: number[]; difficulty_rules: Record<string, unknown> }>) =>
    request<Plan>(`/plans/${id}`, { method: "PATCH", body: JSON.stringify(body) }),

  deletePlan: (id: number) => request<{ ok: boolean }>(`/plans/${id}`, { method: "DELETE" }),

  restartPlan: (id: number) => request<Plan>(`/plans/${id}/restart`, { method: "POST" }),

  progress: (id: number) => request<Progress>(`/plans/${id}/progress`),

  profile: () => request<Profile>("/profile"),
};
