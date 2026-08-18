import { createResource, For, Show } from "solid-js";
import { api } from "../api";

export default function Profile() {
  const [profile] = createResource(() => api.profile());

  return (
    <div>
      <Show when={profile()} fallback={<p>Loading…</p>}>
        {(p) => (
          <>
            <div class="card profile-card">
              <div class="avatar">{initials(p().user.display_name)}</div>
              <div>
                <h1>{p().user.display_name}</h1>
                <p class="hint">
                  {p().user.email} · member for {p().stats.member_days} day{p().stats.member_days === 1 ? "" : "s"}
                </p>
              </div>
            </div>

            <div class="stats">
              <Stat value={p().stats.goals_active} label="Active goals" />
              <Stat value={p().stats.plans_active} label="Active plans" />
              <Stat value={p().stats.best_streak} label="Best streak" />
              <Stat value={p().stats.check_ins_total} label="Check-ins" />
            </div>
          </>
        )}
      </Show>
    </div>
  );
}

function Stat(props: { value: number; label: string }) {
  return (
    <div class="card stat">
      <span class="stat-value">{props.value}</span>
      <span class="stat-label">{props.label}</span>
    </div>
  );
}

function initials(name: string): string {
  return name
    .split(/\s+/)
    .filter(Boolean)
    .map((part) => part[0].toUpperCase())
    .slice(0, 2)
    .join("");
}
