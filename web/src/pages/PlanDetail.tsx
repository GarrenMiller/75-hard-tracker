import { useNavigate, useParams } from "@solidjs/router";
import { createResource, createSignal, For, Show } from "solid-js";
import { api, type Progress } from "../api";
import EditButton from "../components/EditButton";

const STATUS_LABEL: Record<string, string> = {
  active: "Active",
  in_grace: "In grace",
  failed: "Failed",
};

const DAY_STATUS_LABEL: Record<string, string> = {
  completed: "All goals done",
  partial: "Some goals done",
  missed: "No goals done",
  pending: "Today · in progress",
};

export default function PlanDetail() {
  const params = useParams();
  const navigate = useNavigate();
  const [progress, { refetch }] = createResource(() => api.progress(Number(params.id)));
  const [amounts, setAmounts] = createSignal<Record<number, string>>({});
  const [busyGoal, setBusyGoal] = createSignal<number | null>(null);
  const [actionError, setActionError] = createSignal<string | null>(null);
  const [selectedDate, setSelectedDate] = createSignal<string | null>(null);

  const toggleDay = (date: string) =>
    setSelectedDate((cur) => (cur === date ? null : date));

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
      navigate("/plans");
    } catch (err) {
      setActionError(err instanceof Error ? err.message : "Delete failed");
    }
  };

  return (
    <div>
      <Show when={progress()} fallback={<p>Loading…</p>}>
        {(p) => {
          const visibleDays = () => p().days.slice(-30);
          const firstVisibleDay = () => p().days.length - visibleDays().length + 1;
          return (
            <>
              <div class="row">
                <h1>{p().plan.name}</h1>
                <span class={`badge ${p().plan.status}`}>{STATUS_LABEL[p().plan.status] ?? p().plan.status}</span>
              </div>

              <Show when={p().plan.status === "failed"}>
                <div class="banner">
                  <span>This plan failed and is paused.</span>
                  <button onClick={restart}>Restart now</button>
                </div>
              </Show>

              <Show when={p().cycle}>
                <div class={`hero ${p().plan.status}`}>
                  <span class="hero-label">Day</span>
                  <span class="hero-num">
                    {p().cycle!.day}
                    <small> / {p().cycle!.total_days}</small>
                  </span>
                  <span class="hero-sub">
                    <span>
                      <strong>{p().cycle!.missed_days}</strong> missed
                    </span>
                    <span>
                      <strong>{p().plan.cycle_count}</strong> cycle{p().plan.cycle_count === 1 ? "" : "s"}
                    </span>
                    <span>
                      <strong>{p().plan.goal_count}</strong> goal{p().plan.goal_count === 1 ? "" : "s"}
                    </span>
                  </span>
                </div>
              </Show>

              <Show when={p().days.length}>
                <div class="day-strip">
                  <For each={visibleDays()}>
                    {(day) => {
                      const done = day.goals.filter((g) => g.completed).length;
                      const label = DAY_STATUS_LABEL[day.status] ?? day.status;
                      const tip = `Day ${p().days.indexOf(day) + 1} · ${formatShortDate(day.date)} · ${label} · ${done} of ${day.goals.length} goals done`;
                      return (
                        <button
                          type="button"
                          class={`day ${day.status} ${selectedDate() === day.date ? "selected" : ""}`}
                          data-tooltip={tip}
                          aria-label={tip}
                          onClick={() => toggleDay(day.date)}
                        />
                      );
                    }}
                  </For>
                </div>
                <div class="day-ticks">
                  <For each={visibleDays()}>
                    {(_, i) => {
                      const n = firstVisibleDay() + i();
                      return <span>{n === 1 || (n - 1) % 15 === 0 ? `D${n}` : ""}</span>;
                    }}
                  </For>
                </div>
                <div class="legend">
                  <span class="legend-item"><span class="day completed" /> All done</span>
                  <span class="legend-item"><span class="day partial" /> Some done</span>
                  <span class="legend-item"><span class="day missed" /> Missed</span>
                  <span class="legend-item"><span class="day pending" /> Today</span>
                </div>
                <Show when={selectedDate()}>
                  {(() => {
                    const day = p().days.find((d) => d.date === selectedDate());
                    return day ? (
                      <div class="card day-detail">
                        <div class="row">
                          <h3>{formatShortDate(day.date)}</h3>
                          <span class="badge subtle">{DAY_STATUS_LABEL[day.status] ?? day.status}</span>
                        </div>
                        <ul class="day-goals">
                          <For each={day.goals}>
                            {(g) => (
                              <li>
                                <span class={`dot ${g.completed ? "done" : "not-done"}`} />
                                <span class="goal-name">{g.name}</span>
                                <span class="hint">
                                  {g.completed ? "done" : "not done"}
                                  {g.completed ? (() => {
                                    const t = formatDetail({ goal_type_key: g.goal_type_key }, g.detail);
                                    return t ? ` · ${t}` : "";
                                  })() : ""}
                                </span>
                              </li>
                            )}
                          </For>
                        </ul>
                      </div>
                    ) : null;
                  })()}
                </Show>
              </Show>

              <Show when={actionError()}>
                <p class="error">{actionError()}</p>
              </Show>

              <h2 class="section-title">
                <span class="dot plan" />
                Goals
              </h2>
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
                <div class="row">
                  <EditButton planId={p().plan.id} />
                  <button class="danger" onClick={deletePlan}>
                    Delete plan
                  </button>
                </div>
              </div>
            </>
          );
        }}
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

function formatShortDate(value: string): string {
  const [y, m, d] = value.split("-");
  return new Date(Number(y), Number(m) - 1, Number(d)).toLocaleDateString(undefined, {
    month: "short",
    day: "numeric",
  });
}
