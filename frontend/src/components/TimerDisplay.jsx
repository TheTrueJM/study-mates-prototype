const formatTime = (seconds = 0) => {
  const mins = Math.floor(seconds / 60);
  const secs = seconds % 60;
  return `${mins.toString().padStart(2, "0")}:${secs.toString().padStart(2, "0")}`;
};

export default function TimerDisplay({ remaining = 0, running = false, size = "lg", label }) {
  const finished = remaining <= 0;
  const status = finished ? "Time's Up!" : running ? "Time Remaining" : "Timer Paused";

  return (
    <div
      className={`timer-display timer-${size} ${finished ? "is-finished" : ""} ${!running && !finished ? "is-paused" : ""}`}
      role="timer"
      aria-live="off"
    >
      {label && <div className="timer-label">{label}</div>}
      <div className="timer-value">{formatTime(remaining)}</div>
      <div className="timer-status">{status}</div>
    </div>
  );
}
