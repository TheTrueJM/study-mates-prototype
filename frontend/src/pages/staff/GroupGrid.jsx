export default function GroupGrid({ groups = {}, students = {} }) {
  return (
    <div className="group-grid">
      {Object.entries(groups).map(([id, members]) => (
        <div key={id} className="group-card">
          <div className="group-card-header">
            <span>Group {id}</span>
            <span className="group-card-count" aria-label={`${members.length} students`}>{members.length}</span>
          </div>
          <ul className="group-card-body">
            {members.map((member) => (
              <li key={member} className="group-member">{students[member]?.name || "Unknown"}</li>
            ))}
          </ul>
        </div>
      ))}
    </div>
  );
}
