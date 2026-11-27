// A Student's Name and whether they've Disconnected, with a Button to Remove them from the Session
export default function StudentLabel({ id, student, onRemove }) {
  if (!student) return <span className="student-label">Unknown</span>;

  return (
    <>
      <span className="student-label">
        {student.name || "Unknown"}
        {!student.connected && <span className="student-offline">Offline</span>}
      </span>
      {onRemove && (
        <button
          type="button"
          className="student-remove"
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
