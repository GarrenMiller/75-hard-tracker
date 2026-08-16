import { useNavigate } from "@solidjs/router";
import { Show, onMount, type JSX } from "solid-js";
import { loadMe, logout, user } from "./store";
import { getToken } from "./api";

export default function App(props: { children?: JSX.Element }) {
  const navigate = useNavigate();

  onMount(async () => {
    const u = await loadMe();
    if (!u && !getToken()) navigate("/login", { replace: true });
  });

  const onLogout = async () => {
    await logout();
    navigate("/login", { replace: true });
  };

  return (
    <>
      <Show when={user()} fallback={null}>
        <header>
          <a class="brand" href="/">
            75 Hard Tracker
          </a>
          <nav>
            <a href="/">Plans</a>
            <button class="link" onClick={onLogout}>
              Log out ({user()!.display_name})
            </button>
          </nav>
        </header>
      </Show>
      <main>{props.children}</main>
    </>
  );
}
