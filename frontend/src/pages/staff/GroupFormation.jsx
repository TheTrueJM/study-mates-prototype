// GroupFormation - Staff views formed groups and can reform or start discussion
// TODO: Replace dummy data with group formation algorithm results from backend

import Card from '../../components/Card';
import Button from '../../components/Button';

function GroupFormation() {
  // Placeholder data (will come from backend)
  const groups = [
    {
      id: 1,
      members: ['Anonymous-Wombat-42', 'Random-Koala-17', 'Mystery-Dolphin-89', 'Unknown-Eagle-23'],
    },
    {
      id: 2,
      members: ['Silent-Tiger-56', 'Hidden-Panda-91', 'Secret-Fox-34', 'Quiet-Bear-78'],
    },
    {
      id: 3,
      members: ['Private-Owl-12', 'Masked-Wolf-45', 'Veiled-Deer-67', 'Unseen-Hawk-29'],
    },
  ];

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
        <div className="grid grid-cols-3 mb-lg">
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
