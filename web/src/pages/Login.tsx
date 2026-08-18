import { useNavigate } from "@solidjs/router";
import { createSignal, Show } from "solid-js";
import { login } from "../store";
import { ApiError } from "../api";
import Logo from "../components/Logo";

export default function Login() {
  const navigate = useNavigate();
  const [email, setEmail] = createSignal("");
  const [password, setPassword] = createSignal("");
  const [error, setError] = createSignal<string | null>(null);
  const [submitting, setSubmitting] = createSignal(false);

  const onSubmit = async (e: SubmitEvent) => {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await login(email(), password());
      navigate("/", { replace: true });
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Something went wrong");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div class="auth">
      <div class="auth-mark">
        <Logo size={44} />
      </div>
      <form class="card" onSubmit={onSubmit}>
        <h1 class="auth-title">Sign in</h1>
        <p class="tagline">Seventy-five days. No excuses.</p>
        <label>
          Email
          <input
            type="email"
            required
            value={email()}
            onInput={(e) => setEmail(e.currentTarget.value)}
          />
        </label>
        <label>
          Password
          <input
            type="password"
            required
            value={password()}
            onInput={(e) => setPassword(e.currentTarget.value)}
          />
        </label>
        <Show when={error()}>
          <p class="error">{error()}</p>
        </Show>
        <button type="submit" disabled={submitting()}>
          {submitting() ? "Signing in..." : "Sign in"}
        </button>
        <p class="hint">
          No account? <a href="/register">Register</a>
        </p>
      </form>
    </div>
  );
}
