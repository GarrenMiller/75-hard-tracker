export default function Logo(props: { size?: number }) {
  const size = props.size ?? 28;
  return (
    <svg width={size} height={size} viewBox="0 0 48 48" fill="none" aria-hidden="true">
      <circle cx="24" cy="24" r="18" stroke="currentColor" stroke-width="3" />
      <circle cx="24" cy="24" r="11" stroke="currentColor" stroke-width="2" opacity="0.6" />
      <circle cx="24" cy="24" r="4.5" fill="currentColor" />
      <path d="M24 2v7M24 39v7M2 24h7M39 24h7" stroke="currentColor" stroke-width="3" />
    </svg>
  );
}
