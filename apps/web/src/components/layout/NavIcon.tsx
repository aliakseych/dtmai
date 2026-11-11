const PATHS: Record<string, string> = {
  learn: "M3 11l9-8 9 8v9a1 1 0 0 1-1 1h-5v-6H9v6H4a1 1 0 0 1-1-1z",
  practice: "M4 20l4-1L20 7a2.1 2.1 0 0 0-3-3L5 16z",
  mocks: "M6 2h9l5 5v15H6zM14 2v6h6",
  leagues: "M7 3h10v5a5 5 0 0 1-10 0zM5 4H2v2a4 4 0 0 0 4 4M19 4h3v2a4 4 0 0 1-4 4M10 14h4v4h3v3H7v-3h3z",
  quests: "M4 4h16v16H4zM8 12l3 3 5-6",
  profile: "M12 12a5 5 0 1 0 0-10 5 5 0 0 0 0 10zM3 22a9 9 0 0 1 18 0z",
  premium: "M3 8l4 4 5-8 5 8 4-4-2 12H5z",
  more: "M5 10a2 2 0 1 0 0 4 2 2 0 0 0 0-4zM12 10a2 2 0 1 0 0 4 2 2 0 0 0 0-4zM19 10a2 2 0 1 0 0 4 2 2 0 0 0 0-4z",
  lyceums: "M2 9l10-5 10 5-10 5zM6 12v5c0 1.5 3 3 6 3s6-1.5 6-3v-5",
};

export function NavIcon({ name, size = 28 }: { name: keyof typeof PATHS | string; size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" aria-hidden fill="currentColor" stroke="currentColor" strokeWidth={1} strokeLinejoin="round">
      <path d={PATHS[name]} />
    </svg>
  );
}
