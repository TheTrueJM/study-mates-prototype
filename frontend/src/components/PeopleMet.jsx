// The Classmates a Student has Met, with a Button to Shortlist each of them (when Shortlisting is on)
export function ShortlistButton({ person, onToggle, busy = false }) {
  const locked = person.mutual; // A revealed Mutual Shortlist can't be undone

  return (
    <button
      type="button"
      className={`shortlist-button ${person.shortlisted ? "is-on" : ""}`}
      onClick={() => onToggle(person.id, !person.shortlisted)}
      disabled={busy || locked}
      aria-pressed={!!person.shortlisted}
      aria-label={`${person.shortlisted ? "Remove" : "Shortlist"} ${person.name}`}
      title={locked ? "You've both Shortlisted each other" : person.shortlisted ? "Remove from your Shortlist" : "Shortlist as a Potential Teammate"}
    >
      <span aria-hidden="true">{person.shortlisted ? "★" : "☆"}</span>
      <span className="shortlist-button-text">{person.shortlisted ? "Shortlisted" : "Shortlist"}</span>
    </button>
  );
}

const describeMeeting = (person) => [
  `Met ${person.times === 1 ? "Once" : `${person.times} Times`}`,
  person.round ? `Last in Round ${person.round}, Group ${person.group}` : null,
  person.common > 0 ? `${person.common} in Common` : null,
  person.left ? "Has Left" : null,
].filter(Boolean).join(" · ");


export default function PeopleMet({ people = [], shortlisting = false, onToggle, busy = false, empty = "You haven't Met anyone Yet." }) {
  if (!people.length) return <p className="text-muted">{empty}</p>;

  return (
    <ul className="people-list">
      {people.map((person) => (
        <li key={person.id} className={`person ${person.mutual ? "is-mutual" : ""}`}>
          <span className="person-text">
            <span className="person-name">
              {person.name}
              {person.mutual && <span className="tag tag-match">Mutual</span>}
            </span>
            <span className="person-meta">{describeMeeting(person)}</span>
          </span>
          {shortlisting && onToggle && <ShortlistButton person={person} onToggle={onToggle} busy={busy} />}
          {shortlisting && !onToggle && person.shortlisted && !person.mutual && (
            <span className="tag">Shortlisted</span>
          )}
        </li>
      ))}
    </ul>
  );
}
