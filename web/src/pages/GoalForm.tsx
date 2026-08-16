import { useNavigate } from "@solidjs/router";
import { createResource, createSignal, For, Show } from "solid-js";
import { api, ApiError, type GoalType } from "../api";

export default function GoalForm() {
  const navigate = useNavigate();
  const [types] = createResource(() => api.goalTypes());
  const [typeKey, setTypeKey] = createSignal<string | null>(null);
  const [name, setName] = createSignal("");
  const [config, setConfig] = createSignal<Record<string, string | number>>({});
  const [error, setError] = createSignal<string | null>(null);
  const [submitting, setSubmitting] = createSignal(false);

  const type = (): GoalType | undefined => types()?.goal_types.find((t) => t.key === typeKey());

  const setConfigField = (field: string, spec: { type: string }, value: string) => {
    const parsed = spec.type === "number" ? Number(value) : value;
    setConfig((prev) => ({ ...prev, [field]: parsed }));
  };

  const onSubmit = async (e: SubmitEvent) => {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await api.createGoal({
        name: name() || (type()?.name ?? "Goal"),
        goal_type_key: typeKey()!,
        config: config(),
      });
      navigate("/");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Something went wrong");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <form class="card" onSubmit={onSubmit}>
      <h1>New goal</h1>
      <label>
        Goal name
        <input
          value={name()}
          onInput={(e) => setName(e.currentTarget.value)}
          placeholder="Drink a gallon of water"
        />
      </label>
      <label>
        Goal type
        <select value={typeKey() ?? ""} onChange={(e) => setTypeKey(e.currentTarget.value)}>
          <option value="" disabled>
            Select…
          </option>
          <For each={types()?.goal_types}>
            {(t) => <option value={t.key}>{t.name} — {t.description}</option>}
          </For>
        </select>
      </label>
      <Show when={type()}>
        <fieldset>
          <legend>Settings</legend>
          <For each={Object.entries(type()!.config_schema.properties)}>
            {([field, spec]) => (
              <label>
                {spec.title ?? field}
                <input
                  type={spec.type === "number" ? "number" : "text"}
                  required={type()!.config_schema.required.includes(field)}
                  onInput={(e) => setConfigField(field, spec, e.currentTarget.value)}
                />
              </label>
            )}
          </For>
        </fieldset>
      </Show>
      <Show when={error()}>
        <p class="error">{error()}</p>
      </Show>
      <div class="row">
        <a class="link" href="/">
          ← Back
        </a>
        <button type="submit" disabled={submitting() || !typeKey()}>
          {submitting() ? "Creating…" : "Create goal"}
        </button>
      </div>
    </form>
  );
}
