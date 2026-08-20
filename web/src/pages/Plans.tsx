import { useNavigate } from "@solidjs/router";
import { createResource, createSignal, For, Show } from "solid-js";
import { api, type Plan } from "../api";
import EditButton from "../components/EditButton";
import ProgressBar from "../components/ProgressBar";
import PlanForm from "./PlanForm";

const STATUS_LABEL: Record<string, string> = {
  active: "Active",
  in_grace: "In grace",
  failed: "Failed",
};

export default function Plans() {
  const navigate = useNavigate();
  const [plans, { refetch }] = createResource(() => api.listPlans());
  const [showForm, setShowForm] = createSignal(false);
  const [busy, setBusy] = createSignal<number | null>(null);
  const [error, setError] = createSignal<string | null>(null);

  const onSaved = () => {
    setShowForm(false);
    refetch();
  };

  const activate = async (id: number) => {
    setError(null);
    setBusy(id);
    try {
      await api.restartPlan(id);
      refetch();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Activate failed");
    } finally {
      setBusy(null);
    }
  };

  return (
    <div>
      <div class="row">
        <h1>Plans</h1>
        <button onClick={() => setShowForm((v) => !v)}>{showForm() ? "Close" : "New plan"}</button>
      </div>

      <Show when={showForm()}>
        <PlanForm onSaved={onSaved} />
      </Show>

      <Show when={error()}>
        <p class="error">{error()}</p>
      </Show>

      <Show when={plans()?.plans.length} fallback={<Show when={!showForm()}><EmptyPlans onCreate={() => setShowForm(true)} /></Show>}>
        <div class="grid">
          <For each={plans()?.plans}>
            {(plan: Plan) => (
              <div class="card plan-card" onClick={() => navigate(`/plans/${plan.id}`)}>
                <div class="row">
                  <h2>{plan.name}</h2>
                  <div class="row">
                    <span class={`badge ${plan.status}`}>{STATUS_LABEL[plan.status] ?? plan.status}</span>
                    <EditButton planId={plan.id} />
                  </div>
                </div>
                <Show when={plan.cycle_day !== null} fallback={<p class="hint">Paused — activate to restart</p>}>
                  <div class="readout" style={{ padding: "10px 0 4px" }}>
                    <span class="value" style={{ "font-size": "2rem" }}>
                      {plan.cycle_day}
                      <span class="label" style={{ "font-size": "0.7rem", "margin-left": "4px" }}>
                        / {plan.cycle_total_days}
                      </span>
                    </span>
                  </div>
                </Show>
                <ProgressBar day={plan.cycle_day} total={plan.cycle_total_days} />
                <div class="row" style={{ "margin-top": "10px" }}>
                  <p class="hint">
                    {plan.goal_count} goal{plan.goal_count === 1 ? "" : "s"} · cycle #{plan.cycle_count} · started{" "}
                    {formatDate(plan.started_at)}
                  </p>
                  <Show when={plan.status === "failed"}>
                    <button
                      class="link"
                      disabled={busy() === plan.id}
                      onClick={(e) => {
                        e.stopPropagation();
                        activate(plan.id);
                      }}
                    >
                      {busy() === plan.id ? "…" : "Activate"}
                    </button>
                  </Show>
                </div>
              </div>
            )}
          </For>
        </div>
      </Show>
    </div>
  );
}

function EmptyPlans(props: { onCreate: () => void }) {
  return (
    <div class="empty-state">
      <div class="big">No plans yet</div>
      <p class="sub">Define a plan, check in daily, stay disciplined.</p>
      <button onClick={props.onCreate}>Create your first plan</button>
    </div>
  );
}

function formatDate(value: string): string {
  return value.slice(0, 10);
}
