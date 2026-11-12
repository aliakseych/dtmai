import { mediaUrl } from "@/lib/env";

export const DREAM_PLACEHOLDER = "/brand/illus-lyceum-dream.webp";

/** Campus photo cover (placeholder illustration when missing) with the logo overlapping its bottom-left edge. */
export function LyceumCover({ photo, logo, className = "h-32" }: { photo?: string | null; logo?: string | null; className?: string }) {
  return (
    <div className="relative">
      <div className={`overflow-hidden rounded-2xl bg-brand-soft ${className}`}>
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img
          src={photo ? mediaUrl(photo) : DREAM_PLACEHOLDER}
          alt=""
          loading="lazy"
          className={photo ? "h-full w-full object-cover" : "h-full w-full object-contain p-2"}
        />
      </div>
      {logo && (
        // eslint-disable-next-line @next/next/no-img-element
        <img
          src={mediaUrl(logo)}
          alt=""
          loading="lazy"
          className="absolute -bottom-5 left-4 h-14 w-14 rounded-2xl border-2 border-line bg-white object-contain p-1"
        />
      )}
    </div>
  );
}
