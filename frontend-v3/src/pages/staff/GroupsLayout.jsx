import Button from "../../components/Button";


export default function GroupsLayout({ code, students = {}, groups = {}, onGrouping, onDiscussion }) {
  return (
    <>
      <div className="card-subtitle">Group Formation Results</div>

      {/* Group cards in responsive grid */}
      {Object.keys(groups).length === 0 ? (
        <div className="text-center mb-lg">
          <p>No groups formed yet. Click "Reform Groups" to create groups.</p>
        </div>
      ) : (
        <div className="grid grid-cols-3 mb-lg">
          {Object.entries(groups).map(([id, members]) => (
            <div key={id} className="group-card">
              <div className="group-card-header">Group {id}</div>
              <div className="group-card-body">
                {members.map((member) => (
                  <div key={member} className="group-member">{students[member]?.name || "Unknown"}</div>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Action buttons */}
      <div className="btn-group">
        <Button variant="outline" onClick={onGrouping}>Reform Groups</Button>
        <Button variant="secondary" onClick={onDiscussion}>Begin Discussion Time</Button>
      </div>
    </>
  );
}