const PATHS: Record<string, string> = {
  home: "M3 11l9-8 9 8v9a1 1 0 0 1-1 1h-5v-6H9v6H4a1 1 0 0 1-1-1z",
  learn: "M4 3h13a3 3 0 0 1 3 3v15H7a3 3 0 0 1-3-3zM8 8h8M8 12h6",
  plan: "M5 4h14a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2zM7 2v4M17 2v4M3 10h18",
  exam: "M12 2a10 10 0 1 0 0 20 10 10 0 0 0 0-20zM12 17v.01M9.5 9.5a2.5 2.5 0 1 1 3.5 2.3c-.6.3-1 .9-1 1.7",
  practice: "M4 20l4-1L20 7a2.1 2.1 0 0 0-3-3L5 16z",
  mocks: "M6 2h9l5 5v15H6zM14 2v6h6",
  leagues: "M7 3h10v5a5 5 0 0 1-10 0zM5 4H2v2a4 4 0 0 0 4 4M19 4h3v2a4 4 0 0 1-4 4M10 14h4v4h3v3H7v-3h3z",
  quests: "M4 4h16v16H4zM8 12l3 3 5-6",
  profile: "M12 12a5 5 0 1 0 0-10 5 5 0 0 0 0 10zM3 22a9 9 0 0 1 18 0z",
  premium: "M3 8l4 4 5-8 5 8 4-4-2 12H5z",
  more: "M5 10a2 2 0 1 0 0 4 2 2 0 0 0 0-4zM12 10a2 2 0 1 0 0 4 2 2 0 0 0 0-4zM19 10a2 2 0 1 0 0 4 2 2 0 0 0 0-4z",
  lyceums: "M2 9l10-5 10 5-10 5zM6 12v5c0 1.5 3 3 6 3s6-1.5 6-3v-5",
  temur: "M4 4h16v12H9l-5 5z",
};

export function NavIcon({ name, size = 28 }: { name: keyof typeof PATHS | string; size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" aria-hidden fill="currentColor" stroke="currentColor" strokeWidth={1} strokeLinejoin="round">
      <path d={PATHS[name]} />
    </svg>
  );
}
