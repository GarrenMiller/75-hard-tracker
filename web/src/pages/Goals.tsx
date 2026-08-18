import { useNavigate } from "@solidjs/router";
import { createResource, createSignal, For, Show } from "solid-js";
import { api } from "../api";

export default function Goals() {
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
      <div class="row">
        <h1>Goals</h1>
        <button onClick={() => navigate("/goals/new")}>New goal</button>
      </div>

      <Show when={error()}>
        <p class="error">{error()}</p>
      </Show>

      <Show when={profile()} fallback={<p>Loading…</p>}>
        {(p) => (
          <Show
            when={p().goals.length}
            fallback={
              <div class="empty-state">
                <div class="big">No goals yet</div>
                <p class="sub">Goals are the daily targets that make up a plan.</p>
                <button onClick={() => navigate("/goals/new")}>Create your first goal</button>
              </div>
            }
          >
            <div class="list">
              <For each={p().goals}>
                {(item) => {
                  const isQuantity = item.goal.goal_type_key === "daily_quantity";
                  const today = item.goal.today;
                  return (
                    <div class="card goal-row goal-item">
                      <span class="item-icon goal">
                        <IconTarget />
                      </span>
                      <div class="goal-info">
                        <div class="row">
                          <h3>{item.goal.name}</h3>
                          <span class="badge subtle">{item.goal.goal_type_name}</span>
                        </div>
                        <p class="hint">
                          Streak {item.streak} · {item.total_completions} total
                          {item.last_completed_at ? ` · last ${formatDate(item.last_completed_at)}` : ""}
                        </p>
                        <Show when={item.plans.length} fallback={<span class="hint no-plan">Not in a plan</span>}>
                          <div class="goal-plans">
                            <For each={item.plans}>
                              {(p) => {
                                const isActive = p.status === "active" || p.status === "in_grace";
                                return (
                                  <span
                                    class={`badge plan ${isActive ? "" : "paused"}`}
                                    onClick={() => navigate(`/plans/${p.id}`)}
                                  >
                                    {p.name}
                                  </span>
                                );
                              }}
                            </For>
                          </div>
                        </Show>
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
        )}
      </Show>
    </div>
  );
}

function formatDate(value: string): string {
  return value.slice(0, 10);
}

function IconTarget() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
      <circle cx="12" cy="12" r="9" />
      <circle cx="12" cy="12" r="5" />
      <circle cx="12" cy="12" r="1" />
    </svg>
  );
}
