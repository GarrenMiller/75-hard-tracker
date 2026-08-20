import { For } from "solid-js";
import type { GoalType } from "../api";

export default function QuantityInput(props: {
  units?: GoalType["units"];
  goalUnit: string;
  amount: string;
  unit: string;
  onAmount: (value: string) => void;
  onUnit: (value: string) => void;
}) {
  const options = () => {
    const all = props.units ?? { volume: [], weight: [] };
    return all.volume.includes(props.goalUnit) ? all.volume : all.weight;
  };
  return (
    <span class="quantity-input">
      <input
        type="number"
        min="0"
        step="any"
        placeholder="amount"
        value={props.amount}
        onInput={(e) => props.onAmount(e.currentTarget.value)}
      />
      <select value={props.unit} onInput={(e) => props.onUnit(e.currentTarget.value)}>
        <For each={options()}>
          {(opt) => <option value={opt}>{opt}</option>}
        </For>
      </select>
    </span>
  );
}
