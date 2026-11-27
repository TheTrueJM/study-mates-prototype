import StudentLabel from "./StudentLabel";


export default function GroupGrid({ groups = {}, students = {}, onRemove }) {
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
              <li key={member} className={`group-member ${students[member]?.connected ? "" : "is-disconnected"}`}>
                <StudentLabel id={member} student={students[member]} onRemove={onRemove} />
              </li>
            ))}
          </ul>
        </div>
      ))}
    </div>
  );
}
