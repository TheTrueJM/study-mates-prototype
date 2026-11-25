import Button from "../../components/Button";
import TimerDisplay from "../../components/TimerDisplay";
import QuestionList from "../../components/QuestionList";

import GroupGrid from "./GroupGrid";


export default function DiscussionLayout({
  questions = [], timeRemaining = 0, timeDuration = 0, timeRunning = false, students = {}, groups = {},
  onGrouping, onStartTimer, onStopTimer, onResetTimer, busy = "",
}) {
  const finished = timeRemaining <= 0;
  const untouched = !timeRunning && timeRemaining === timeDuration;

  return (
    <div className="stack">
      <div className="discussion-timer">
        <TimerDisplay remaining={timeRemaining} running={timeRunning} size="xl" />
        <div className="btn-group mt-sm">
          {timeRunning ? (
            <Button variant="outline" onClick={onStopTimer}>Pause Timer</Button>
          ) : (
            <Button variant="secondary" onClick={onStartTimer}>
              {finished ? "Restart Timer" : untouched ? "Start Timer" : "Resume Timer"}
            </Button>
          )}
          <Button variant="outline" onClick={onResetTimer} disabled={untouched}>Reset Timer</Button>
        </div>
      </div>

      <section>
        <h2 className="section-title">Discussion Prompts</h2>
        <QuestionList questions={questions} />
      </section>

      <details className="disclosure">
        <summary>Show Groups ({Object.keys(groups).length})</summary>
        <div className="disclosure-body">
          <GroupGrid groups={groups} students={students} />
        </div>
      </details>

      <Button variant="primary" fullWidth onClick={onGrouping} disabled={!!busy}>
        {busy === "grouping" ? "Forming Groups…" : "Next Group Round"}
      </Button>
    </div>
  );
}
