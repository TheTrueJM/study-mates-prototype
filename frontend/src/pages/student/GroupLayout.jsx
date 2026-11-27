import { useCountdown } from "../../hooks/useCountdown";

import Button from "../../components/Button";
import TimerDisplay from "../../components/TimerDisplay";
import QuestionList from "../../components/QuestionList";

import MemberCard from "./MemberCard";


export default function GroupLayout({
  state, username, round = 0, groupNumber, groupMembers = [], attributes, availableAttributes = [], attributesComplete,
  questions = [], timeRemaining, timeRunning, timeEndsAt, onEdit,
}) {
  const remaining = useCountdown(timeRemaining, timeEndsAt);

  const canEdit = availableAttributes.length > 0;

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

  return (
    <div className="stack">
      <div className="group-hero">
        <span className="group-hero-label">{round > 0 && `Round ${round} · `}Your Group</span>
        <span className="group-hero-number">{groupNumber}</span>
        <p className="group-hero-text">
          {state === "discussion"
            ? "Discussion Time! Get to know your Group Members."
            : "Find your Group Members below and Sit Together."}
        </p>
      </div>

      {state === "discussion" && (
        <TimerDisplay remaining={remaining} running={timeRunning} size="md" />
      )}

      {canEdit && !attributesComplete && (
        <div className="callout">
          <p>You haven't Finished adding your Details. Add them so your Group can get to Know You.</p>
          <Button size="sm" onClick={onEdit}>Add details</Button>
        </div>
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
            />
          ))}
        </div>
      </section>

      {canEdit && (
        <Button variant="outline" fullWidth onClick={onEdit}>Edit my Details</Button>
      )}
    </div>
  );
}
