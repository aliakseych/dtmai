"use client";
import { Button, Card, Mascot } from "@dtmai/ui";
import { useT } from "@dtmai/i18n";

/** Final screen: placement test for the first chosen subject, or skip. */
export function PlacementStep({ subjectName, busy, error, isGuest, onStart, onSkip, onBack }: { subjectName: string; busy: boolean; error: boolean; isGuest: boolean; onStart: () => void; onSkip: () => void; onBack: () => void }) {
  const t = useT();
  return (
    <div className="mx-auto flex min-h-dvh max-w-xl flex-col justify-center gap-5 px-4 py-6">
      <Mascot mood="celebrate" size={140} alt={t("mascot.alt")} className="mx-auto h-auto w-32" />
      <Card className="text-center">
        <h1 className="text-2xl">{t("onb.placement.for", { subject: subjectName })}</h1>
        <p className="text-ink-soft">{t("onb.placement.text")}</p>
        {isGuest && <p className="mt-1 text-sm text-ink-soft">{t("onb.guestNote")}</p>}
      </Card>
      {error && (
        <p role="alert" className="text-center font-bold text-red-deep">
          {t("common.error")}
        </p>
      )}
      <Button block disabled={busy} onClick={onStart}>
        {t("onb.placement.start")}
      </Button>
      <Button block variant="secondary" disabled={busy} onClick={onSkip}>
        {t("onb.placement.skip")}
      </Button>
      <Button variant="ghost" onClick={onBack}>
        {t("common.back")}
      </Button>
    </div>
  );
}
