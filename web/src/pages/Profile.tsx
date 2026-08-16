import { useNavigate } from "@solidjs/router";
import { createResource, createSignal, For, Show } from "solid-js";
import { api } from "../api";

const STATUS_LABEL: Record<string, string> = {
  active: "Active",
  in_grace: "In grace",
  failed: "Failed",
};

export default function Profile() {
  const navigate = useNavigate();
  const [profile, { refetch }] = createResource(() => api.profile());
  const [amounts, setAmounts] = createSignal<Record<number, string>>({});
  const [busyGoal, setBusyGoal] = createSignal<number | null>(null);
  const [error, setError] = createSignal<string | null>(null);

  const setAmount = (goalId: number, value: string) =>
    setAmounts((prev) => ({ ...prev, [goalId]: value }));

  const checkIn = async (goalId: number, isQuantity: boolean) => {
    setError(null);
    setBusyGoal(goalId);
    try {
      const value = isQuantity ? { amount: Number(amounts()[goalId] ?? 1) } : {};
      await api.createCheckIn(goalId, { value });
      refetch();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Check-in failed");
    } finally {
      setBusyGoal(null);
    }
  };

  return (
    <div>
      <Show when={profile()} fallback={<p>Loading…</p>}>
        {(p) => (
          <>
            <div class="card profile-card">
              <div class="avatar">{initials(p().user.display_name)}</div>
              <div>
                <h1>{p().user.display_name}</h1>
                <p class="hint">
                  {p().user.email} · member for {p().stats.member_days} day{p().stats.member_days === 1 ? "" : "s"}
                </p>
              </div>
            </div>

            <div class="stats">
              <Stat value={p().stats.goals_total} label="Goals" />
              <Stat value={p().stats.goals_active} label="Active goals" />
              <Stat value={p().stats.plans_active} label="Active plans" />
              <Stat value={p().stats.best_streak} label="Best streak" />
              <Stat value={p().stats.check_ins_total} label="Check-ins" />
            </div>

            <Show when={error()}>
              <p class="error">{error()}</p>
            </Show>

            <Show when={p().plans.length}>
              <h2>Plans</h2>
              <div class="list">
                <For each={p().plans}>
                  {(item) => (
                    <div class="card goal-row" onClick={() => navigate(`/plans/${item.plan.id}`)}>
                      <div class="goal-info">
                        <div class="row">
                          <h3>{item.plan.name}</h3>
                          <span class={`badge ${item.plan.status}`}>
                            {STATUS_LABEL[item.plan.status] ?? item.plan.status}
                          </span>
                        </div>
                        <p class="hint">
                          {item.cycle_day !== null
                            ? `Day ${item.cycle_day} of ${item.cycle_total_days}`
                            : "Failed — restart from plan page"}
                          {" · "}
                          {item.plan.goal_count} goals · cycle #{item.plan.cycle_count}
                        </p>
                      </div>
                    </div>
                  )}
                </For>
              </div>
            </Show>

            <Show when={p().goals.length}>
              <h2>Goals</h2>
              <div class="list">
                <For each={p().goals}>
                  {(item) => {
                    const isQuantity = item.goal.goal_type_key === "daily_quantity";
                    const today = item.goal.today;
                    return (
                      <div class="card goal-row">
                        <div class="goal-info">
                          <div class="row">
                            <h3>{item.goal.name}</h3>
                            <span class="badge subtle">{item.goal.goal_type_name}</span>
                          </div>
                          <p class="hint">
                            Streak {item.streak} · {item.total_completions} total
                            {item.last_completed_at ? ` · last ${formatDate(item.last_completed_at)}` : ""}
                          </p>
                        </div>
                        <div class="goal-action">
                          <Show when={today?.completed}>
                            <span class="badge success">Done today</span>
                          </Show>
                          <Show when={!today?.completed}>
                            <Show when={isQuantity}>
                              <input
                                type="number"
                                min="0"
                                step="any"
                                placeholder="amount"
                                value={amounts()[item.goal.id] ?? ""}
                                onInput={(e) => setAmount(item.goal.id, e.currentTarget.value)}
                              />
                            </Show>
                            <button
                              disabled={busyGoal() === item.goal.id}
                              onClick={() => checkIn(item.goal.id, isQuantity)}
                            >
                              {busyGoal() === item.goal.id ? "…" : "Check in"}
                            </button>
                          </Show>
                        </div>
                      </div>
                    );
                  }}
                </For>
              </div>
            </Show>
          </>
        )}
      </Show>
    </div>
  );
}

function Stat(props: { value: number; label: string }) {
  return (
    <div class="card stat">
      <span class="stat-value">{props.value}</span>
      <span class="stat-label">{props.label}</span>
    </div>
  );
}

function initials(name: string): string {
  return name
    .split(/\s+/)
    .filter(Boolean)
    .map((part) => part[0].toUpperCase())
    .slice(0, 2)
    .join("");
}

function formatDate(value: string): string {
  return value.slice(0, 10);
}
