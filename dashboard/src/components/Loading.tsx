export function Loading({ label = "Loading…" }: { label?: string }) {
  return <p className="loading">{label}</p>;
}
