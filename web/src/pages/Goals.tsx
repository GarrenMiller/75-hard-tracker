import { useNavigate } from "@solidjs/router";
import { createResource, createSignal, For, Show } from "solid-js";
import { api } from "../api";
import GoalForm from "./GoalForm";

export default function Goals() {
  const navigate = useNavigate();
  const [profile, { refetch }] = createResource(() => api.profile());
  const [showForm, setShowForm] = createSignal(false);

  const onSaved = () => {
    setShowForm(false);
    refetch();
  };

  return (
    <div>
      <div class="row">
        <h1>Goals</h1>
        <button onClick={() => setShowForm((v) => !v)}>{showForm() ? "Close" : "New goal"}</button>
      </div>

      <Show when={showForm()}>
        <GoalForm onSaved={onSaved} />
      </Show>

      <Show when={profile()} fallback={<p>Loading…</p>}>
        {(p) => (
          <Show
            when={p().goals.length}
            fallback={
              <Show when={!showForm()}>
                <div class="empty-state">
                  <div class="big">No goals yet</div>
                  <p class="sub">Goals are the daily targets that make up a plan.</p>
                  <button onClick={() => setShowForm(true)}>Create your first goal</button>
                </div>
              </Show>
            }
          >
            <div class="list">
              <For each={p().goals}>
                {(item) => {
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
