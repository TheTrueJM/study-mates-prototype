import { useEffect, useRef, useState } from "react";

import { useCountdown } from "../../hooks/useCountdown";

import Button from "../../components/Button";
import TimerDisplay from "../../components/TimerDisplay";
import QuestionList from "../../components/QuestionList";

import GroupGrid from "./GroupGrid";


const ADJUSTMENT = 30; // Seconds (mirrors TIMER_ADJUSTMENT in backend/app/sockets/staff.py)
const ADJUSTMENT_SHOWN = 1500; // Milliseconds

const formatAdjustment = (seconds) => {
  const sign = seconds < 0 ? "−" : "+";
  const total = Math.abs(seconds);
  return total < 60 ? `${sign}${total} Sec` : `${sign}${Math.floor(total / 60)}:${String(total % 60).padStart(2, "0")}`;
};


// The Introductions (a short countdown which rolls into the Discussion) and the Discussion itself
export default function DiscussionLayout({
  introduction = false, questions = [], timeRemaining = 0, timeDuration = 0, timeRunning = false, timeEndsAt = null,
  students = {}, groups = {},
  onGrouping, onStartTimer, onStopTimer, onResetTimer, onAdjustTimer, onSkipIntroduction, onRemoveStudent, busy = "",
}) {
  const remaining = useCountdown(timeRemaining, timeEndsAt);

  // Briefly shows the time Added or Removed, totalling quick presses together
  const [adjusted, setAdjusted] = useState(null); // { id, seconds }
  const hideTimeout = useRef(null);

  useEffect(() => () => clearTimeout(hideTimeout.current), []);

  const adjust = async (seconds) => {
    const response = await onAdjustTimer(seconds);
    if (!response?.ok) return;

    setAdjusted((current) => ({ id: Date.now(), seconds: (current?.seconds ?? 0) + seconds }));
    clearTimeout(hideTimeout.current);
    hideTimeout.current = setTimeout(() => setAdjusted(null), ADJUSTMENT_SHOWN);
  };

  const finished = remaining <= 0;
  const untouched = !timeRunning && remaining === timeDuration;

  const prompts = <QuestionList questions={questions} />;

  return (
    <div className="stack">
      {introduction && (
        <div className="phase-banner">
          <h2 className="phase-title">Introductions</h2>
          <p className="phase-text">
            Take turns sharing your Name, and which App Name is yours. The Discussion starts automatically afterwards.
          </p>
        </div>
      )}

      <div className="discussion-timer">
        <div className="discussion-timer-display">
          <TimerDisplay remaining={remaining} running={timeRunning} size="xl" label={introduction ? "Introductions" : undefined} />
          <span className="timer-adjusted" aria-live="polite">
            {adjusted && (
              <span key={adjusted.id} className={adjusted.seconds < 0 ? "is-removed" : ""}>
                {formatAdjustment(adjusted.seconds)}
              </span>
            )}
          </span>
        </div>
        <div className="btn-group timer-controls mt-sm">
          {timeRunning ? (
            <Button variant="outline" onClick={onStopTimer}>Pause Timer</Button>
          ) : (
            <Button variant="secondary" onClick={onStartTimer}>
              {finished ? "Restart Timer" : untouched ? "Start Timer" : "Resume Timer"}
            </Button>
          )}
          <div className="timer-adjust">
            <Button variant="outline" onClick={() => adjust(-ADJUSTMENT)} disabled={finished} aria-label="Remove 30 Seconds">
              −30 Sec
            </Button>
            <Button variant="outline" onClick={() => adjust(ADJUSTMENT)} aria-label="Add 30 Seconds">
              +30 Sec
            </Button>
          </div>
          {introduction ? (
            <Button variant="outline" onClick={onSkipIntroduction} disabled={!!busy}>
              {busy === "skip" ? "Starting…" : "Start Discussion"}
            </Button>
          ) : (
            <Button variant="outline" onClick={onResetTimer} disabled={untouched}>Reset Timer</Button>
          )}
        </div>
      </div>

      {introduction ? (
        <details className="disclosure">
          <summary>Preview the Discussion Prompts</summary>
          <div className="disclosure-body">{prompts}</div>
        </details>
      ) : (
        <section>
          <h2 className="section-title">Discussion Prompts</h2>
          {prompts}
        </section>
      )}

      <details className="disclosure">
        <summary>Show Groups ({Object.keys(groups).length})</summary>
        <div className="disclosure-body">
          <GroupGrid groups={groups} students={students} onRemove={onRemoveStudent} />
        </div>
      </details>

      <Button variant="primary" fullWidth onClick={onGrouping} disabled={!!busy}>
        {busy === "grouping" ? "Forming Groups…" : "Next Group Round"}
      </Button>
    </div>
  );
}
