import { createResource, createSignal, For, Show } from "solid-js";
import { api } from "../api";

export default function TodayCard(props: { onCheckedIn?: () => void }) {
  const [profile, { refetch }] = createResource(() => api.profile());
  const [amounts, setAmounts] = createSignal<Record<number, string>>({});
  const [busy, setBusy] = createSignal<number | null>(null);

  const setAmount = (goalId: number, value: string) =>
    setAmounts((prev) => ({ ...prev, [goalId]: value }));

  const checkIn = async (goalId: number, isQuantity: boolean) => {
    setBusy(goalId);
    try {
      const value = isQuantity ? { amount: Number(amounts()[goalId] ?? 1) } : {};
      await api.createCheckIn(goalId, { value });
      await refetch();
      props.onCheckedIn?.();
    } finally {
      setBusy(null);
    }
  };

  const activeGoals = () => profile()?.goals.filter((g) => g.goal.active) ?? [];
  const done = () => activeGoals().filter((g) => g.goal.today?.completed).length;
  const open = () => activeGoals().filter((g) => !g.goal.today?.completed).length;

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
            when={activeGoals().length}
            fallback={<p class="hint">No goals yet. Create a goal to start tracking.</p>}
          >
            <ul class="today-goals">
              <For each={activeGoals()}>
                {(item) => {
                  const g = item.goal;
                  const isQuantity = g.goal_type_key === "daily_quantity";
                  const detail = g.today?.detail ?? {};
                  const detailText = formatDetail(g.goal_type_key, detail);
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
                      <Show when={detailText}>
                        <span class="hint">{detailText}</span>
                      </Show>
                      <Show when={!g.today?.completed}>
                        <Show when={isQuantity}>
                          <input
                            type="number"
                            min="0"
                            step="any"
                            placeholder="amount"
                            value={amounts()[g.id] ?? ""}
                            onInput={(e) => setAmount(g.id, e.currentTarget.value)}
                          />
                        </Show>
                        <button
                          class="link"
                          disabled={busy() === g.id}
                          onClick={() => checkIn(g.id, isQuantity)}
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
