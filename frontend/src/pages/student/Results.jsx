import { useState } from "react";
import { Link } from "react-router-dom";

import { clearResults, connectedFirst, loadResults, removeResults } from "../../results";

import Card from "../../components/Card";
import Button from "../../components/Button";
import ConfirmDialog from "../../components/ConfirmDialog";
import PeopleMet, { ConnectedBanner } from "../../components/PeopleMet";


const formatDate = (time) => new Date(time).toLocaleString(undefined, {
  weekday: "short", day: "numeric", month: "short", hour: "numeric", minute: "2-digit",
});


// A Student's Past Sessions, kept on their Device, so they can find the Classmates they Met (and were Connected with)
function Results() {
  const [results, setResults] = useState(loadResults);
  const [confirmClear, setConfirmClear] = useState(false);

  const remove = (key) => {
    removeResults(key);
    setResults(loadResults());
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
          <Button variant="danger" size="sm" onClick={() => setConfirmClear(true)}>Clear All</Button>
        )}
      >
        {results.length === 0 ? (
          <div className="empty-state">
            <p className="mb-sm">No Saved Sessions Yet. Once you Meet your Group in a Session, it'll be Saved here.</p>
            <Link to="/" className="btn btn-primary btn-sm">Join a Session</Link>
          </div>
        ) : (
          <div className="stack">
            {results.map((session) => {
              const connections = session.people.filter((person) => person.mutual).length;

              return (
                <section key={session.key} className="result-session">
                  <div className="section-header">
                    <div>
                      <h2 className="section-title">{session.tutorialName}</h2>
                      <p className="text-muted">
                        {formatDate(session.updatedAt)} · You were <strong>{session.studentName}</strong>
                      </p>
                    </div>
                    <Button variant="outline" size="sm" onClick={() => remove(session.key)} aria-label={`Remove ${session.tutorialName}`}>
                      Remove
                    </Button>
                  </div>

                  <h3 className="result-heading">People You Met ({session.people.length})</h3>
                  {session.shortlisting && <ConnectedBanner count={connections} past />}
                  <PeopleMet people={connectedFirst(session.people)} shortlisting={session.shortlisting} />
                </section>
              );
            })}
          </div>
        )}

        {results.length > 0 && (
          <p className="text-center mt-md"><Link to="/">Join Another Session</Link></p>
        )}
      </Card>

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
