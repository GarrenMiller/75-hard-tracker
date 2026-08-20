import { A, useNavigate } from "@solidjs/router";
import { Show } from "solid-js";
import { logout, user } from "../store";

export default function Sidebar(props: { open: boolean; onClose: () => void }) {
  const navigate = useNavigate();

  const onLogout = async () => {
    await logout();
    navigate("/login", { replace: true });
  };

  const closeOnMobile = () => {
    if (window.matchMedia("(max-width: 720px)").matches) props.onClose();
  };

  return (
    <>
      <Show when={props.open}>
        <div class="backdrop" onClick={props.onClose} />
      </Show>
      <aside class={`sidebar ${props.open ? "open" : ""}`}>
        <nav class="sidebar-nav">
          <A href="/" end activeClass="active" onClick={closeOnMobile}>
            <IconGrid />
            <span class="label">Dashboard</span>
          </A>
          <A href="/plans" activeClass="active" onClick={closeOnMobile}>
            <IconClipboard />
            <span class="label">Plans</span>
          </A>
          <A href="/goals" activeClass="active" onClick={closeOnMobile}>
            <IconTarget />
            <span class="label">Goals</span>
          </A>
        </nav>
        <div class="sidebar-footer">
          <Show when={user()} fallback={null}>
            <div class="sidebar-user">
              <span class="avatar small">{initials(user()!.display_name)}</span>
              <span class="label">{user()!.display_name}</span>
            </div>
            <button class="sidebar-icon" onClick={onLogout} title="Log out" aria-label="Log out">
              <IconLogout />
            </button>
          </Show>
        </div>
      </aside>
    </>
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

function IconGrid() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
      <rect x="3" y="3" width="7" height="7" rx="1" />
      <rect x="14" y="3" width="7" height="7" rx="1" />
      <rect x="3" y="14" width="7" height="7" rx="1" />
      <rect x="14" y="14" width="7" height="7" rx="1" />
    </svg>
  );
}

function IconClipboard() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
      <rect x="8" y="2" width="8" height="4" rx="1" />
      <path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2" />
    </svg>
  );
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

function IconLogout() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
      <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
      <path d="M16 17l5-5-5-5" />
      <path d="M21 12H9" />
    </svg>
  );
}
