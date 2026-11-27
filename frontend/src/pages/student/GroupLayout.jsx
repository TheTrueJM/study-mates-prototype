import { useCountdown } from "../../hooks/useCountdown";

import Button from "../../components/Button";
import TimerDisplay from "../../components/TimerDisplay";
import QuestionList from "../../components/QuestionList";

import PeopleMet from "../../components/PeopleMet";

import MemberCard from "./MemberCard";


export default function GroupLayout({
  state, username, round = 0, groupNumber, groupMembers = [], attributes, availableAttributes = [], attributesComplete,
  questions = [], timeRemaining, timeRunning, timeEndsAt, onEdit, history = [], shortlisting = false, onShortlist,
  seating = null, tableNumbering = false,
}) {
  const remaining = useCountdown(timeRemaining, timeEndsAt);

  const hasDetails = availableAttributes.length > 0;
  const canEdit = hasDetails || !!seating;
  const introduction = state === "introduction";
  const timed = introduction || state === "discussion";

  if (groupNumber === null || groupNumber === undefined) {
    return (
      <div className="waiting">
        <h2 className="waiting-title">Groups are being Formed…</h2>
        <div className="loading-dots" aria-hidden="true">
          <div className="dot" />
          <div className="dot" />
          <div className="dot" />
        </div>
        <p className="text-muted">You'll see your Group here as soon as you're Placed In One.</p>
      </div>
    );
  }

  // Show the Student First, then the rest of the Group Members
  const members = [...groupMembers].sort((a, b) => (b.name === username) - (a.name === username));

  // Students staying at their Table are Grouped there, so their Classmates come to them
  const seatedTable = seating?.staySeated ? seating.table : null;
  const seatedHere = seatedTable !== null && seatedTable === groupNumber;
  const seatedElsewhere = seatedTable !== null && seatedTable !== groupNumber;

  const findingText = seatedHere
    ? `Stay where you are at Table ${seatedTable}. Your Group will come to you.`
    : tableNumbering
      ? `Head to Table ${groupNumber} and Sit Together with your Group.`
      : "Find your Group Members below and Sit Together.";

  return (
    <div className="stack">
      <div className="group-hero">
        <span className="group-hero-label">{round > 0 && `Round ${round} · `}Your Group</span>
        <span className="group-hero-number">{groupNumber}</span>
        <p className="group-hero-text">
          {introduction
            ? "Introductions! Take Turns to Share Your Name and a little About Yourself."
            : state === "discussion"
              ? "Discussion Time! Get to know your Group Members."
              : findingText}
        </p>
      </div>

      {seatedElsewhere && (
        <div className="callout callout-info" role="status">
          <p>
            You're staying at Table {seatedTable}. Your Tutor can see this and may Move Classmates to you.
            Otherwise, your Group will be Formed at your Table from the Next Round.
          </p>
        </div>
      )}

      {timed && (
        <TimerDisplay
          remaining={remaining}
          running={timeRunning}
          size="md"
          label={introduction ? "Introductions" : undefined}
        />
      )}

      {hasDetails && !attributesComplete && (
        <div className="callout">
          <p>You haven't Finished adding your Details. Add them so your Group can get to Know You.</p>
          <Button size="sm" onClick={onEdit}>Add details</Button>
        </div>
      )}

      {introduction && (
        <details className="disclosure">
          <summary>Preview the Discussion Prompts</summary>
          <div className="disclosure-body"><QuestionList questions={questions} /></div>
        </details>
      )}

      {state === "discussion" && (
        <section>
          <h2 className="section-title">Discussion Prompts</h2>
          <QuestionList questions={questions} />
        </section>
      )}

      <section>
        <div className="section-header">
          <h2 className="section-title">Group Members ({members.length})</h2>
          <span className="section-hint">Select a Member to see their Details</span>
        </div>
        <div className="member-list">
          {members.map((member) => (
            <MemberCard
              key={member.name}
              member={member}
              isSelf={member.name === username}
              ownAttributes={attributes}
              shortlisting={shortlisting}
              onShortlist={onShortlist}
            />
          ))}
        </div>
        {shortlisting && (
          <p className="section-hint mt-xs">
            Connect with anyone you'd like to Team Up with. If they Connect with you too, you'll both be notified at the End of the Session.
          </p>
        )}
      </section>

      <PreviousPeople history={history} groupMembers={members} shortlisting={shortlisting} onShortlist={onShortlist} />

      {canEdit && (
        <Button variant="outline" fullWidth onClick={onEdit}>{hasDetails ? "Edit my Details" : "Seating Needs"}</Button>
      )}
    </div>
  );
}


// Classmates Met in Previous Rounds (not including the Current Group)
export function PreviousPeople({ history = [], groupMembers = [], shortlisting = false, onShortlist }) {
  const current = new Set(groupMembers.map((member) => member.id));
  const previous = history.filter((person) => !current.has(person.id));
  if (!previous.length) return null;

  return (
    <details className="disclosure">
      <summary>People You've Met ({previous.length})</summary>
      <div className="disclosure-body">
        <PeopleMet people={previous} shortlisting={shortlisting} onToggle={onShortlist} />
      </div>
    </details>
  );
}
