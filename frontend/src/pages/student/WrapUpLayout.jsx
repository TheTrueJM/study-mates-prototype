import { Link } from "react-router-dom";

import { useCountdown } from "../../hooks/useCountdown";

import TimerDisplay from "../../components/TimerDisplay";
import PeopleMet from "../../components/PeopleMet";


// Shown once the Tutorial has Ended, until the Tutor Closes the Session
export default function WrapUpLayout({
  timeRemaining, timeRunning, timeEndsAt, history = [], shortlisting = false, onShortlist,
}) {
  const remaining = useCountdown(timeRemaining, timeEndsAt);
  const mutuals = history.filter((person) => person.mutual);

  return (
    <div className="stack">
      <div className="group-hero">
        <span className="group-hero-label">Session Complete</span>
        <span className="group-hero-title">That's a Wrap!</span>
        <p className="group-hero-text">Thanks for Taking Part. Head back to your Original Seat and get your things Ready.</p>
      </div>

      <TimerDisplay
        remaining={remaining}
        running={timeRunning}
        size="md"
        label="Wrap-Up"
        finishedText="Your Tutor will Close the Session Soon"
      />

      {shortlisting && mutuals.length > 0 && (
        <section className="mutual-panel">
          <h2 className="section-title">Mutual Shortlists</h2>
          <p className="text-muted mb-xs">You both want to Team Up! Go and find them to swap Details.</p>
          <PeopleMet people={mutuals} shortlisting />
        </section>
      )}

      <div className="callout">
        <p>
          {shortlisting
            ? "Before you go, Shortlist anyone else you'd like to Team Up with. If they Shortlist you too, you'll both be notified straight away."
            : "Before you go, think about who you Met today. If you'd like to Team Up or keep Talking with anyone, now's a great time to go and swap Details."}
        </p>
      </div>

      <section>
        <h2 className="section-title">People You Met ({history.length})</h2>
        <PeopleMet people={history} shortlisting={shortlisting} onToggle={onShortlist} />
        {history.length > 0 && (
          <p className="section-hint mt-xs">
            This is Saved to this Device, so you can still see it once the Session Closes (in <Link to="/results">Past Sessions</Link>).
          </p>
        )}
      </section>
    </div>
  );
}
