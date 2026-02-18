// GroupFormation - Staff views formed groups and can reform or start discussion
// TODO: Replace dummy data with group formation algorithm results from backend

import Card from '../../components/Card';
import Button from '../../components/Button';

function GroupFormation() {
  // Stress-test: 8 groups x 4 members
  const groups = Array.from({ length: 8 }, (_, i) => ({
    id: i + 1,
    members: Array.from({ length: 4 }, (_, j) =>
      `Student-${String(i * 4 + j + 1).padStart(2, '0')}`
    ),
  }));

  const handleReform = () => {
    console.log('Reform groups');
    // TODO: Call API -> re-run group formation
  };

  const handleBeginDiscussion = () => {
    console.log('Begin discussion time');
    // TODO: Call API -> navigate to /staff/discussion
  };

  return (
    <div className="page">
      <div className="container container-lg">
      <Card title="Tutorial Session ABCD-1234">
        <div className="card-subtitle">Group Formation Result</div>

        {/* Group cards in responsive grid */}
        <div className="grid grid-cols-4 mb-sm">
          {groups.map((group) => (
            <div key={group.id} className="group-card">
              <div className="group-card-header">Group {group.id}</div>
              <div className="group-card-body">
                {group.members.map((member) => (
                  <div key={member} className="group-member">{member}</div>
                ))}
              </div>
            </div>
          ))}
        </div>

        {/* Action buttons */}
        <div className="btn-group">
          <Button variant="outline" onClick={handleReform}>
            Reform Groups
          </Button>
          <Button variant="secondary" onClick={handleBeginDiscussion}>
            Begin Discussion Time
          </Button>
        </div>

      </Card>
      </div>
    </div>
  );
}

export default GroupFormation;
