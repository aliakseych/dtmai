import { cn } from "../cn";

export function Avatar({ name, src, size = 48, className }: { name: string; src?: string | null; size?: number; className?: string }) {
  const initials = name.trim().slice(0, 2).toUpperCase() || "?";
  return src ? (
    <img src={src} alt={name} width={size} height={size} className={cn("rounded-full object-cover", className)} style={{ width: size, height: size }} />
  ) : (
    <span
      role="img"
      aria-label={name}
      className={cn("grid place-items-center rounded-full bg-blue font-extrabold text-white", className)}
      style={{ width: size, height: size, fontSize: size * 0.4 }}
    >
      {initials}
    </span>
  );
}
