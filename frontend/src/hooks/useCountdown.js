import { useEffect, useState } from "react";

const TICK = 250;


/**
 * Seconds Remaining of a Timer, counted down by itself while the Timer is running (`endsAt` is set),
 * as the server only sends an update when the Timer changes.
 */
export function useCountdown(remaining, endsAt) {
  const [now, setNow] = useState(() => Date.now());

  useEffect(() => {
    if (!endsAt) return;

    const interval = setInterval(() => setNow(Date.now()), TICK);
    return () => clearInterval(interval);
  }, [endsAt]);

  const seconds = endsAt ? Math.min(remaining, (endsAt - now) / 1000) : remaining;
  return Math.max(0, Math.ceil(seconds));
}
