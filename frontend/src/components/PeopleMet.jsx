// The Classmates a Student has Met, with a Button to Connect with each of them (when Connections are on).
// Students who Connect with each other are Connected, which is revealed to both at the Wrap-Up.
export function ConnectButton({ person, onToggle, busy = false }) {
  const connected = person.mutual; // A revealed Connection can't be undone
  const requested = person.shortlisted;

  return (
    <button
      type="button"
      className={`connect-button ${connected ? "is-connected" : requested ? "is-on" : ""}`}
      onClick={() => onToggle(person.id, !requested)}
      disabled={busy || connected}
      aria-pressed={!!requested}
      aria-label={connected ? `Connected with ${person.name}` : requested ? `Cancel Request to ${person.name}` : `Connect with ${person.name}`}
      title={connected ? "You're Connected" : requested ? "Cancel your Request" : "Ask to Connect as Potential Teammates"}
    >
      <span aria-hidden="true">{requested || connected ? "✓" : "+"}</span>
      <span className="connect-button-text">{connected ? "Connected" : requested ? "Requested" : "Connect"}</span>
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
            <span className="person-name">{person.name}</span>
            <span className="person-meta">{describeMeeting(person)}</span>
          </span>
          {shortlisting && onToggle && <ConnectButton person={person} onToggle={onToggle} busy={busy} />}
          {shortlisting && !onToggle && (person.mutual || person.shortlisted) && (
            <span className={`tag ${person.mutual ? "tag-match" : ""}`}>{person.mutual ? "Connected" : "Requested"}</span>
          )}
        </li>
      ))}
    </ul>
  );
}


// A short Message about the Classmates a Student is Connected with (shown above the list of People they Met)
export function ConnectedBanner({ count, past = false }) {
  if (!count) return null;
  const classmates = count === 1 ? "1 Classmate" : `${count} Classmates`;

  return (
    <p className="connected-banner" role="status">
      <span>
        <strong>{past ? "You were" : "You're"} Connected with {classmates}!</strong>
        <br/>
        Both you and {count == 1 ? "this person" : "these people"} want to Team Up! Go and find them to swap Details.
      </span>
    </p>
  );
}
