import { Show } from "solid-js";

export default function ProgressBar(props: { day: number | null; total: number | null }) {
  return (
    <Show when={props.day !== null && props.total !== null}>
      <div
        class="progress"
        title={`Day ${props.day} of ${props.total}`}
      >
        <div
          class="progress-fill"
          style={{ width: `${Math.min(100, (props.day! / props.total!) * 100)}%` }}
        />
      </div>
      <p class="hint progress-label">
        Day {props.day} of {props.total}
      </p>
    </Show>
  );
}
