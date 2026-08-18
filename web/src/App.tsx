import { useNavigate } from "@solidjs/router";
import { createSignal, Show, onMount, type JSX } from "solid-js";
import { loadMe, user } from "./store";
import { getToken } from "./api";
import Sidebar from "./components/Sidebar";
import Logo from "./components/Logo";

export default function App(props: { children?: JSX.Element }) {
  const navigate = useNavigate();
  const [open, setOpen] = createSignal(localStorage.getItem("sidebar-open") !== "0");

  onMount(async () => {
    const u = await loadMe();
    if (!u && !getToken()) navigate("/login", { replace: true });
  });

  const toggle = () => {
    setOpen((v) => {
      const next = !v;
      localStorage.setItem("sidebar-open", next ? "1" : "0");
      return next;
    });
  };

  return (
    <Show when={user()} fallback={<main>{props.children}</main>}>
      <Sidebar open={open()} onClose={() => setOpen(false)} />
      <div class={`shell ${open() ? "sidebar-open" : ""}`}>
        <header>
          <button class="hamburger" onClick={toggle} aria-label="Toggle navigation" aria-expanded={open()}>
            <IconMenu />
          </button>
          <a class="brand" href="/">
            <span style={{ color: "var(--accent)" }}>
              <Logo size={26} />
            </span>
            <span class="wordmark">
              75 HARD
              <small>TRACKER</small>
            </span>
          </a>
        </header>
        <main>{props.children}</main>
      </div>
    </Show>
  );
}

function IconMenu() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
      <path d="M4 6h16M4 12h16M4 18h16" />
    </svg>
  );
}
