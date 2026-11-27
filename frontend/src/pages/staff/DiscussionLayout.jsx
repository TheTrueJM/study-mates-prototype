import Button from "../../components/Button";
import TimerPanel from "../../components/TimerPanel";
import QuestionList from "../../components/QuestionList";

import GroupGrid from "./GroupGrid";


// The Introductions (a short countdown which rolls into the Discussion) and the Discussion itself
export default function DiscussionLayout({
  introduction = false, questions = [], timer, students = {}, groups = {}, maxGroups = null,
  onGrouping, onResetTimer, onSkipIntroduction, onRemoveStudent, onMoveStudent, busy = "",
}) {
  const prompts = <QuestionList questions={questions} />;

  return (
    <div className="stack">
      {introduction && (
        <div className="phase-banner">
          <h2 className="phase-title">Introductions</h2>
          <p className="phase-text">
            Take Turns to Introduce Yourself and Share Names. The Discussion will begin immediately afterwards.
          </p>
        </div>
      )}

      <TimerPanel
        {...timer}
        label={introduction ? "Introductions" : undefined}
        action={(remaining, untouched) => introduction ? (
          <Button variant="outline" onClick={onSkipIntroduction} disabled={!!busy}>
            {busy === "skip" ? "Starting…" : "Start Discussion"}
          </Button>
        ) : (
          <Button variant="outline" onClick={onResetTimer} disabled={untouched}>Reset Timer</Button>
        )}
      />

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
          <GroupGrid
            groups={groups}
            students={students}
            maxGroups={maxGroups}
            onRemove={onRemoveStudent}
            onMove={onMoveStudent}
          />
        </div>
      </details>

      <Button variant="primary" fullWidth onClick={onGrouping} disabled={!!busy}>
        {busy === "grouping" ? "Forming Groups…" : "Next Group Round"}
      </Button>
    </div>
  );
}
