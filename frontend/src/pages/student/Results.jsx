import { useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";

import { clearResults, connectedFirst, loadResults, removeResults } from "../../results";

import Card from "../../components/Card";
import Button from "../../components/Button";
import ConfirmDialog from "../../components/ConfirmDialog";
import PeopleMet, { ConnectedBanner } from "../../components/PeopleMet";


const formatDate = (time) => new Date(time).toLocaleString(undefined, {
  weekday: "short", day: "numeric", month: "short", hour: "numeric", minute: "2-digit",
});


// One Past Session, which expands to show the Classmates the Student Met (and was Connected with)
function SessionResult({ session, open, onToggle, onRemove }) {
  const connections = session.people.filter((person) => person.mutual).length;
  const bodyId = `session-${session.key}`;

  return (
    <li className={`result-card ${open ? "is-open" : ""}`}>
      <div className="result-card-top">
        <button
          type="button"
          className="result-card-header"
          aria-expanded={open}
          aria-controls={bodyId}
          onClick={onToggle}
        >
          <span className="result-card-summary">
            <span className="result-card-text">
              <span className="result-card-title">{session.tutorialName}</span>
              <span className="result-card-meta">
                {formatDate(session.updatedAt)} · You were <strong>{session.studentName}</strong>
              </span>
            </span>
            <span className="result-card-tags">
              <span className="tag">{session.people.length} Met</span>
              {session.shortlisting && connections > 0 && <span className="tag tag-match">{connections} Connected</span>}
            </span>
          </span>
          <span className="sr-only">{open ? "Hide" : "Show"} Who You Met</span>
          <span className={`chevron ${open ? "is-open" : ""}`} aria-hidden="true" />
        </button>
        <button
          type="button"
          className="student-action student-remove result-card-remove"
          onClick={onRemove}
          aria-label={`Remove ${session.tutorialName}`}
          title="Remove from this Device"
        >
          &times;
        </button>
      </div>

      {open && (
        <div className="result-card-body" id={bodyId}>
          {session.shortlisting && <ConnectedBanner count={connections} past />}
          <PeopleMet people={connectedFirst(session.people)} shortlisting={session.shortlisting} />
        </div>
      )}
    </li>
  );
}


// A Student's Past Sessions, kept on their Device, so they can find the Classmates they Met (and were Connected with)
function Results() {
  const navigate = useNavigate();
  const location = useLocation();

  const [results, setResults] = useState(loadResults);
  // A Session that just Closed is shown straight away
  const [open, setOpen] = useState(() => new Set(location.state?.justClosed && results[0] ? [results[0].key] : []));
  const [removing, setRemoving] = useState(null); // Session to Remove (awaiting confirmation)
  const [confirmClear, setConfirmClear] = useState(false);

  const toggle = (key) => setOpen((current) => {
    const next = new Set(current);
    if (next.has(key)) next.delete(key);
    else next.add(key);
    return next;
  });

  const remove = () => {
    removeResults(removing.key);
    setResults(loadResults());
    setRemoving(null);
  };

  const clear = () => {
    clearResults();
    setResults([]);
    setConfirmClear(false);
  };

  return (
    <div className="container container-md page">
      <Card
        title="Your Past Sessions"
        subtitle="Who You Met, Saved on this Device Only."
        actions={results.length > 0 && (
          <Button variant="primary" size="sm" onClick={() => navigate("/")}>Join Another Session</Button>
        )}
      >
        {results.length === 0 ? (
          <div className="empty-state">
            <p className="mb-sm">No Saved Sessions Yet. Once you Meet your Group in a Session, it'll be Saved here.</p>
            <Button variant="primary" size="sm" onClick={() => navigate("/")}>Join a Session</Button>
          </div>
        ) : (
          <>
            <p className="section-hint mb-xs">Select a Session to see Who You Met.</p>
            <ul className="result-list">
              {results.map((session) => (
                <SessionResult
                  key={session.key}
                  session={session}
                  open={open.has(session.key)}
                  onToggle={() => toggle(session.key)}
                  onRemove={() => setRemoving(session)}
                />
              ))}
            </ul>
            {results.length > 1 && (
              <div className="result-footer">
                <Button variant="subtle" size="sm" onClick={() => setConfirmClear(true)}>Clear All Sessions</Button>
              </div>
            )}
          </>
        )}
      </Card>

      <ConfirmDialog
        isOpen={!!removing}
        title={`Remove ${removing?.tutorialName ?? "this Session"}?`}
        message="Everyone you Met in this Session will be Removed from this Device."
        confirmLabel="Remove Session"
        danger
        onConfirm={remove}
        onCancel={() => setRemoving(null)}
      />

      <ConfirmDialog
        isOpen={confirmClear}
        title="Clear All Past Sessions?"
        message="Everyone you Met in your Past Sessions will be Removed from this Device."
        confirmLabel="Clear All"
        danger
        onConfirm={clear}
        onCancel={() => setConfirmClear(false)}
      />
    </div>
  );
}

export default Results;
