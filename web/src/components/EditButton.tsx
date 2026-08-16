import { useNavigate } from "@solidjs/router";

export default function EditButton(props: { planId: number }) {
  const navigate = useNavigate();

  return (
    <button
      type="button"
      class="icon-btn"
      title="Edit plan"
      aria-label="Edit plan"
      onClick={(e) => {
        e.stopPropagation();
        navigate(`/plans/${props.planId}/edit`);
      }}
    >
      <IconPencil />
    </button>
  );
}

function IconPencil() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
      <path d="M12 20h9" />
      <path d="M16.5 3.5a2.1 2.1 0 0 1 3 3L7 19l-4 1 1-4Z" />
    </svg>
  );
}
