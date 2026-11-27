import Button from "../../components/Button";
import TimerPanel from "../../components/TimerPanel";


// Shown once the Tutorial has Ended, giving everyone time to Return to their Seats before the Session Closes
export default function WrapUpLayout({
  timer, round = 0, studentCount = 0, shortlisting = false, mutualPairs = 0, onResetTimer, onClose,
}) {
  return (
    <div className="stack">
      <div className="phase-banner">
        <h2 className="phase-title">That's a Wrap!</h2>
        <p className="phase-text">
          Thanks for Taking Part! Head back to your Original Seats and get your things Ready.
          Before you go, think about who you Met, and swap Details with anyone you'd like to Team Up with.
        </p>
      </div>

      <TimerPanel
        {...timer}
        label="Wrap-Up"
        finishedText="Wrap-Up Time is Over"
        action={(remaining, untouched) => (
          <Button variant="outline" onClick={onResetTimer} disabled={untouched}>Reset Timer</Button>
        )}
      />

      <p className="text-muted text-center">
        {round} Round{round === 1 ? "" : "s"} · {studentCount} Student{studentCount === 1 ? "" : "s"}
        {shortlisting && ` · ${mutualPairs} Mutual Shortlist${mutualPairs === 1 ? "" : "s"}`}.
        The Countdown is only a Guide, so the Session stays Open until you Close it.
      </p>

      <Button variant="danger" fullWidth onClick={onClose}>Close Session</Button>
    </div>
  );
}
