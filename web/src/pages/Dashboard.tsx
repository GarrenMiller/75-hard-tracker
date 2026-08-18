import { useNavigate } from "@solidjs/router";
import { createResource, For, Show } from "solid-js";
import { api, type Plan } from "../api";
import EditButton from "../components/EditButton";
import ProgressBar from "../components/ProgressBar";
import TodayCard from "../components/TodayCard";

const STATUS_LABEL: Record<string, string> = {
  active: "Active",
  in_grace: "In grace",
  failed: "Failed",
};

export default function Dashboard() {
  const navigate = useNavigate();
  const [plans, { refetch }] = createResource(() => api.listPlans());

  return (
    <div>
      <div class="row">
        <h1>Plans</h1>
        <button onClick={() => navigate("/plans/new")}>New plan</button>
      </div>

      <TodayCard onCheckedIn={() => refetch()} />

      <Show when={plans()?.plans.length} fallback={<EmptyPlans onCreate={() => navigate("/plans/new")} />}>
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
                <Show when={plan.cycle_day !== null} fallback={<p class="hint">Failed — restart from plan page</p>}>
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
                <p class="hint">
                  {plan.goal_count} goal{plan.goal_count === 1 ? "" : "s"} · cycle #{plan.cycle_count} · started{" "}
                  {formatDate(plan.started_at)}
                </p>
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
