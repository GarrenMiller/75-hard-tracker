import { useNavigate } from "@solidjs/router";
import { createResource, For, Show } from "solid-js";
import { api, type Plan } from "../api";
import EditButton from "../components/EditButton";
import ProgressBar from "../components/ProgressBar";

const STATUS_LABEL: Record<string, string> = {
  active: "Active",
  in_grace: "In grace",
  failed: "Failed",
};

export default function Dashboard() {
  const navigate = useNavigate();
  const [plans] = createResource(() => api.listPlans());

  return (
    <div>
      <div class="row">
        <h1>Plans</h1>
        <button onClick={() => navigate("/plans/new")}>New plan</button>
      </div>
      <Show when={plans()?.plans.length} fallback={<p class="hint">No plans yet. Create one to get started.</p>}>
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
                <p>{plan.goal_count} goals · cycle #{plan.cycle_count}</p>
                <ProgressBar day={plan.cycle_day} total={plan.cycle_total_days} />
                <p class="hint">Started {formatDate(plan.started_at)}</p>
              </div>
            )}
          </For>
        </div>
      </Show>
    </div>
  );
}

function formatDate(value: string): string {
  return value.slice(0, 10);
}
