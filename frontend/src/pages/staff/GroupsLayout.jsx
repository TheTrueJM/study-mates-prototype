// GroupsLayout - Staff sees formed groups and can choose to reform them or start the discussion
import Button from '../../components/Button';

export default function GroupsLayout({ groups = [], students = {}, onGrouping, onDiscussion }) {
  return (
    <>
      <div className="card-subtitle">Group Formation Results</div>

      {/* Group cards in responsive grid */}
      {groups.length === 0 ? (
        <div className="text-center mb-lg">
          <p>No groups formed yet. Click "Reform Groups" to create groups.</p>
        </div>
      ) : (
        <div className="grid grid-cols-3 mb-lg">
          {groups.map((group) => (
            <div key={group.id} className="group-card">
              <div className="group-card-header">Group {group.id}</div>
              <div className="group-card-body">
                {group.members.map((member) => (
                  <div key={member} className="group-member">{students[member]?.name || member}</div>
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
