import { useNavigate } from "@solidjs/router";
import { createResource, createSignal, For, Show } from "solid-js";
import { api, type Goal } from "../api";
import QuantityInput from "./QuantityInput";

export default function TodayCard(props: { onCheckedIn?: () => void }) {
  const navigate = useNavigate();
  const [profile, { refetch }] = createResource(() => api.profile());
  const [goalTypes] = createResource(() => api.goalTypes());
  const [amounts, setAmounts] = createSignal<Record<number, string>>({});
  const [units, setUnits] = createSignal<Record<number, string>>({});
  const [busy, setBusy] = createSignal<number | null>(null);

  const quantityUnits = () =>
    goalTypes()?.goal_types.find((t) => t.key === "daily_quantity")?.units;

  const setAmount = (goalId: number, value: string) =>
    setAmounts((prev) => ({ ...prev, [goalId]: value }));

  const setUnit = (goalId: number, value: string) =>
    setUnits((prev) => ({ ...prev, [goalId]: value }));

  const goalUnit = (goal: Goal) => String(goal.config.unit ?? "");

  const checkIn = async (goal: Goal, isQuantity: boolean, planId?: number) => {
    setBusy(goal.id);
    try {
      const value = isQuantity
        ? { amount: Number(amounts()[goal.id] ?? 1), unit: units()[goal.id] ?? goalUnit(goal) }
        : {};
      await api.createCheckIn(goal.id, { value, plan_id: planId });
      await refetch();
      props.onCheckedIn?.();
    } finally {
      setBusy(null);
    }
  };

  const trackedGoals = () =>
    (profile()?.goals ?? []).filter(
      (g) =>
        g.goal.active &&
        g.plans.some((p) => p.status === "active" || p.status === "in_grace"),
    );
  const done = () => trackedGoals().filter((g) => g.goal.today?.completed).length;
  const open = () => trackedGoals().filter((g) => !g.goal.today?.completed).length;

  return (
    <Show when={profile()}>
      {(p) => (
        <div class="card today-card">
          <div class="today-header">
            <h2>Today</h2>
            <span class="today-date">
              {new Date().toLocaleDateString(undefined, {
                weekday: "long",
                month: "long",
                day: "numeric",
              })}
            </span>
          </div>
          <div class="today-stats">
            <div class="readout">
              <span class="value">{done()}</span>
              <span class="label">Done</span>
            </div>
            <div class="readout">
              <span class="value">{open()}</span>
              <span class="label">Open</span>
            </div>
            <div class="readout">
              <span class="value">{p().stats.best_streak}</span>
              <span class="label">Best streak</span>
            </div>
          </div>
          <Show
            when={trackedGoals().length}
            fallback={<p class="hint">No active plans. Create or restart a plan to start tracking.</p>}
          >
            <ul class="today-goals">
              <For each={trackedGoals()}>
                {(item) => {
                  const g = item.goal;
                  const isQuantity = g.goal_type_key === "daily_quantity";
                  const detail = g.today?.detail ?? {};
                  const detailText = formatDetail(g.goal_type_key, detail);
                  const activePlans = item.plans.filter(
                    (p) => p.status === "active" || p.status === "in_grace",
                  );
                  const planId = activePlans.length ? activePlans[0].id : undefined;
                  return (
                    <li class={`today-goal ${g.today?.completed ? "done" : ""}`}>
                      <span class="today-check">
                        <Show when={g.today?.completed} fallback={null}>
                          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round">
                            <path d="M20 6 9 17l-5-5" />
                          </svg>
                        </Show>
                      </span>
                      <span class="today-goal-name">{g.name}</span>
                      <span class="today-goal-plans">
                        <For each={activePlans}>
                          {(p) => (
                            <span
                              class="badge plan"
                              onClick={() => navigate(`/plans/${p.id}`)}
                            >
                              {p.name}
                            </span>
                          )}
                        </For>
                      </span>
                      <Show when={detailText}>
                        <span class="hint">{detailText}</span>
                      </Show>
                        <Show when={!g.today?.completed}>
                          <Show when={isQuantity}>
                            <QuantityInput
                              units={quantityUnits()}
                              goalUnit={goalUnit(g)}
                              amount={amounts()[g.id] ?? ""}
                              unit={units()[g.id] ?? goalUnit(g)}
                              onAmount={(v) => setAmount(g.id, v)}
                              onUnit={(v) => setUnit(g.id, v)}
                            />
                          </Show>
                          <button
                            class="link"
                            disabled={busy() === g.id}
                            onClick={() => checkIn(g, isQuantity, planId)}
                          >
                            {busy() === g.id ? "…" : "Check in"}
                          </button>
                        </Show>
                      <Show when={g.today?.completed}>
                        <span class="badge success">Done</span>
                      </Show>
                    </li>
                  );
                }}
              </For>
            </ul>
          </Show>
        </div>
      )}
    </Show>
  );
}

function formatDetail(goalTypeKey: string, detail: Record<string, unknown>): string {
  if (goalTypeKey === "daily_quantity" && detail.current !== undefined) {
    return `${detail.current} / ${detail.target} ${detail.unit}`;
  }
  if (goalTypeKey === "weekly_frequency" && detail.count !== undefined) {
    return `${detail.count} / ${detail.times_per_week} this week`;
  }
  return "";
}
