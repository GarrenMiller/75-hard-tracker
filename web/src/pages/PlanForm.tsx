import { useNavigate, useParams } from "@solidjs/router";
import { createEffect, createResource, createSignal, For, Show } from "solid-js";
import { api, ApiError, type Plan } from "../api";

export default function PlanForm(props: { onSaved?: (plan: Plan) => void }) {
  const navigate = useNavigate();
  const params = useParams();
  const planId = props.onSaved ? null : params.id ? Number(params.id) : null;
  const [plan] = createResource(() => (planId ? api.getPlan(planId) : Promise.resolve(null)));
  const [goals] = createResource(() => api.listGoals());

  const [name, setName] = createSignal("");
  const [selected, setSelected] = createSignal<number[]>([]);
  const [duration, setDuration] = createSignal(75);
  const [policy, setPolicy] = createSignal<"restart_on_fail" | "grace_days">("restart_on_fail");
  const [grace, setGrace] = createSignal(0);
  const [error, setError] = createSignal<string | null>(null);
  const [submitting, setSubmitting] = createSignal(false);

  let prefilled = false;
  createEffect(() => {
    const p = plan();
    if (p && !prefilled) {
      prefilled = true;
      setName(p.name);
      setDuration(p.difficulty_rules.duration_days);
      setPolicy(p.difficulty_rules.lapse_policy);
      setGrace(p.difficulty_rules.grace_days);
      setSelected((p.goals ?? []).map((g) => g.id));
    }
  });

  const toggle = (id: number) =>
    setSelected((prev) =>
      prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id],
    );

  const onSubmit = async (e: SubmitEvent) => {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      const body = {
        name: name() || "My plan",
        goal_ids: selected(),
        difficulty_rules: {
          duration_days: duration(),
          lapse_policy: policy(),
          grace_days: grace(),
        },
      };
      const saved = planId ? await api.updatePlan(planId, body) : await api.createPlan(body);
      if (props.onSaved) {
        props.onSaved(saved);
        setName("");
        setSelected([]);
        setDuration(75);
        setPolicy("restart_on_fail");
        setGrace(0);
      } else {
        navigate(`/plans/${saved.id}`);
      }
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Something went wrong");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <form class="card" onSubmit={onSubmit}>
      <h1>{planId ? "Edit plan" : "New plan"}</h1>
      <label>
        Plan name
        <input value={name()} onInput={(e) => setName(e.currentTarget.value)} placeholder="75 Hard" />
      </label>
      <label>
        Duration (days)
        <input
          type="number"
          min="1"
          value={duration()}
          onInput={(e) => setDuration(Number(e.currentTarget.value))}
        />
      </label>
      <fieldset>
        <legend>Failure policy</legend>
        <label class="radio">
          <input
            type="radio"
            name="policy"
            checked={policy() === "restart_on_fail"}
            onChange={() => setPolicy("restart_on_fail")}
          />
          Restart plan when any goal lapses
        </label>
        <label class="radio">
          <input
            type="radio"
            name="policy"
            checked={policy() === "grace_days"}
            onChange={() => setPolicy("grace_days")}
          />
          Allow grace days before failing
        </label>
        <Show when={policy() === "grace_days"}>
          <label>
            Grace days
            <input
              type="number"
              min="0"
              value={grace()}
              onInput={(e) => setGrace(Number(e.currentTarget.value))}
            />
          </label>
        </Show>
      </fieldset>
      <fieldset>
        <legend>Goals</legend>
        <Show when={goals()?.goals.length === 0} fallback={null}>
          <p class="hint">No goals yet. Create some goals on the Goals page first.</p>
        </Show>
        <For each={goals()?.goals}>
          {(goal) => (
            <label class="radio">
              <input
                type="checkbox"
                checked={selected().includes(goal.id)}
                onChange={() => toggle(goal.id)}
              />
              {goal.name} ({goal.goal_type_name})
            </label>
          )}
        </For>
      </fieldset>
      <Show when={error()}>
        <p class="error">{error()}</p>
      </Show>
      <div class="row">
        <Show when={!props.onSaved}>
          <a class="link" href="/plans">
            ← Back
          </a>
        </Show>
        <button type="submit" disabled={submitting()}>
          {submitting() ? "Saving…" : planId ? "Save changes" : "Create plan"}
        </button>
      </div>
    </form>
  );
}
