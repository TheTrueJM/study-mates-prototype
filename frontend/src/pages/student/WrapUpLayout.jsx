import { useCountdown } from "../../hooks/useCountdown";

import TimerDisplay from "../../components/TimerDisplay";


// Shown once the Tutorial has Ended, until the Tutor Closes the Session
export default function WrapUpLayout({ timeRemaining, timeRunning, timeEndsAt }) {
  const remaining = useCountdown(timeRemaining, timeEndsAt);

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

      <div className="callout">
        <p>
          Before you go, think about who you Met today. If you'd like to Team Up or keep Talking with anyone,
          now's a great time to go and swap Details.
        </p>
      </div>
    </div>
  );
}
