import Button from "../../components/Button";


export default function DiscussionLayout({ code, questions = [], timeRemaining = 0, timeRunning = false, onGrouping, onStartTimer, onStopTimer }) {
  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, "0")}:${secs.toString().padStart(2, "0")}`;
  };


  return (
    <>
      <div className="card-subtitle">Group Discussion</div>

      {/* Timer display */}
      <div className="form-group">
        <label className="input-label">Time Remaining</label>
        <div className="timer-display">
          <div className="timer-value">{formatTime(timeRemaining)}</div>
          <div className="timer-status">{timeRunning ? "Timer Running" : "Timer Ready"}</div>
        </div>
      </div>

      {/* Discussion questions */}
      <div className="mb-md">
        <label className="input-label">Discussion Topics and Questions</label>
        <div className="flex-col gap-xs" style={{ display: "flex" }}>
          {questions.map((question, index) => (
            <div key={index} className="question-item">
              <div className="question-number">{index + 1}</div>
              <div>{question}</div>
            </div>
          ))}
        </div>
      </div>

      <div className="btn-group">
        {!timeRunning ? (
          <Button variant="secondary" onClick={onStartTimer}>Resume Discussion Timer</Button>
        ) : (
          <Button variant="outline" onClick={onStopTimer}>Pause Discussion Timer</Button>
        )}
        <Button variant="primary" onClick={onGrouping}>Next Group Forming Round</Button>
      </div>
    </>
  );
}