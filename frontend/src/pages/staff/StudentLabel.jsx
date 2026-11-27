// A Student's Name and whether they've Disconnected, with Buttons to Move them to another Group or Remove them
export default function StudentLabel({ id, student, onRemove, onMove, moving = false }) {
  if (!student) return <span className="student-label">Unknown</span>;

  return (
    <>
      <span className="student-label">
        {student.name || "Unknown"}
        {!student.connected && <span className="student-offline">Offline</span>}
      </span>
      {onMove && (
        <button
          type="button"
          className={`student-action student-move ${moving ? "is-active" : ""}`}
          onClick={() => onMove(id)}
          aria-label={`Move ${student.name}`}
          aria-expanded={moving}
          title="Move to Another Group"
        >
          &#8644;
        </button>
      )}
      {onRemove && (
        <button
          type="button"
          className="student-action student-remove"
          onClick={() => onRemove(id)}
          aria-label={`Remove ${student.name}`}
          title="Remove from Session"
        >
          &times;
        </button>
      )}
    </>
  );
}
