import { cn } from "../cn";

export type MascotMood =
  | "straight" | "wave" | "celebrate" | "sad" | "thinking" | "sleep"
  | "streak" | "trophy" | "premium" | "left" | "right" | "top"
  | "reading" | "calendar" | "rush" | "chat" | "point" | "lock" | "question";

/** Images are served by the consuming app at <basePath>/temur-<mood>.webp */
export function Mascot({
  mood = "straight",
  size = 160,
  alt,
  basePath = "/brand",
  className,
}: {
  mood?: MascotMood;
  size?: number;
  alt: string;
  basePath?: string;
  className?: string;
}) {
  return (
    <img
      src={`${basePath}/temur-${mood}.webp`}
      alt={alt}
      width={size}
      height={size}
      className={cn("select-none object-contain", className)}
      draggable={false}
    />
  );
}
