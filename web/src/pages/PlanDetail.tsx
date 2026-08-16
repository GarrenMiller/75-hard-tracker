import { useNavigate, useParams } from "@solidjs/router";
import { createResource, createSignal, For, Show } from "solid-js";
import { api, type Progress } from "../api";

const STATUS_LABEL: Record<string, string> = {
  active: "Active",
  in_grace: "In grace",
  failed: "Failed",
};

export default function PlanDetail() {
  const params = useParams();
  const navigate = useNavigate();
  const [progress, { refetch }] = createResource(() => api.progress(Number(params.id)));
  const [amounts, setAmounts] = createSignal<Record<number, string>>({});
  const [busyGoal, setBusyGoal] = createSignal<number | null>(null);
  const [actionError, setActionError] = createSignal<string | null>(null);

  const setAmount = (goalId: number, value: string) =>
    setAmounts((prev) => ({ ...prev, [goalId]: value }));

  const checkIn = async (goalId: number, isQuantity: boolean) => {
    setActionError(null);
    setBusyGoal(goalId);
    try {
      const value = isQuantity ? { amount: Number(amounts()[goalId] ?? 1) } : {};
      await api.createCheckIn(goalId, { value });
      refetch();
    } catch (err) {
      setActionError(err instanceof Error ? err.message : "Check-in failed");
    } finally {
      setBusyGoal(null);
    }
  };

  const restart = async () => {
    setActionError(null);
    try {
      await api.restartPlan(Number(params.id));
      refetch();
    } catch (err) {
      setActionError(err instanceof Error ? err.message : "Restart failed");
    }
  };

  const deletePlan = async () => {
    if (!confirm("Delete this plan?")) return;
    try {
      await api.deletePlan(Number(params.id));
      navigate("/");
    } catch (err) {
      setActionError(err instanceof Error ? err.message : "Delete failed");
    }
  };

  return (
    <div>
      <Show when={progress()} fallback={<p>Loading…</p>}>
        {(p) => (
          <>
            <div class="row">
              <h1>{p().plan.name}</h1>
              <span class={`badge ${p().plan.status}`}>{STATUS_LABEL[p().plan.status] ?? p().plan.status}</span>
            </div>
            <Show when={p().plan.status === "failed"}>
              <p class="error">
                This plan failed and is paused.{" "}
                <button onClick={restart}>Restart now</button>
              </p>
            </Show>
            <Show when={p().cycle}>
              <div class="stats">
                <div class="card stat">
                  <span class="stat-value">
                    {p().cycle!.day}<small>/{p().cycle!.total_days}</small>
                  </span>
                  <span class="stat-label">Day</span>
                </div>
                <div class="card stat">
                  <span class="stat-value">{p().cycle!.missed_days}</span>
                  <span class="stat-label">Missed days</span>
                </div>
                <div class="card stat">
                  <span class="stat-value">{p().plan.cycle_count}</span>
                  <span class="stat-label">Cycles</span>
                </div>
              </div>
            </Show>

            <Show when={p().days.length}>
              <div class="day-strip">
                <For each={p().days.slice(-30)}>
                  {(day) => (
                    <span
                      class={`day ${day.status}`}
                      title={`${day.date}: ${day.status}`}
                    />
                  )}
                </For>
              </div>
            </Show>

            <Show when={actionError()}>
              <p class="error">{actionError()}</p>
            </Show>

            <h2>Goals</h2>
            <div class="list">
              <For each={p().goals}>
                {(item) => {
                  const isQuantity = item.goal.goal_type_key === "daily_quantity";
                  const detail = item.today?.detail ?? {};
                  const detailText = formatDetail(item.goal, detail);
                  return (
                    <div class="card goal-row">
                      <div class="goal-info">
                        <div class="row">
                          <h3>{item.goal.name}</h3>
                          <span class="badge subtle">{item.goal.goal_type_name}</span>
                        </div>
                        <p class="hint">
                          Streak {item.streak} day{item.streak === 1 ? "" : "s"}
                          {detailText ? ` · ${detailText}` : ""}
                        </p>
                      </div>
                      <div class="goal-action">
                        <Show when={item.today.completed}>
                          <span class="badge success">Done today</span>
                        </Show>
                        <Show when={!item.today.completed}>
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

            <div class="row footer-actions">
              <a class="link" href="/">
                ← Back
              </a>
              <button class="danger" onClick={deletePlan}>
                Delete plan
              </button>
            </div>
          </>
        )}
      </Show>
    </div>
  );
}

function formatDetail(goal: { goal_type_key: string }, detail: Record<string, unknown>): string {
  if (goal.goal_type_key === "daily_quantity" && detail.current !== undefined) {
    return `${detail.current} / ${detail.target} ${detail.unit}`;
  }
  if (goal.goal_type_key === "weekly_frequency" && detail.count !== undefined) {
    return `${detail.count} / ${detail.times_per_week} this week`;
  }
  return "";
}
