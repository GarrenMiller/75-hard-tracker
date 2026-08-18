import { useNavigate } from "@solidjs/router";
import { createSignal, Show } from "solid-js";
import { register } from "../store";
import { ApiError } from "../api";
import Logo from "../components/Logo";

export default function Register() {
  const navigate = useNavigate();
  const [email, setEmail] = createSignal("");
  const [password, setPassword] = createSignal("");
  const [displayName, setDisplayName] = createSignal("");
  const [error, setError] = createSignal<string | null>(null);
  const [submitting, setSubmitting] = createSignal(false);

  const onSubmit = async (e: SubmitEvent) => {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await register(email(), password(), displayName());
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
        <h1 class="auth-title">Create account</h1>
        <p class="tagline">Seventy-five days. No excuses.</p>
        <label>
          Display name
          <input
            required
            value={displayName()}
            onInput={(e) => setDisplayName(e.currentTarget.value)}
          />
        </label>
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
          Password (8+ characters)
          <input
            type="password"
            required
            minLength={8}
            value={password()}
            onInput={(e) => setPassword(e.currentTarget.value)}
          />
        </label>
        <Show when={error()}>
          <p class="error">{error()}</p>
        </Show>
        <button type="submit" disabled={submitting()}>
          {submitting() ? "Creating..." : "Create account"}
        </button>
        <p class="hint">
          Already have an account? <a href="/login">Sign in</a>
        </p>
      </form>
    </div>
  );
}
