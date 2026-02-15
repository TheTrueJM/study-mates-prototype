// GroupFormation - Staff views formed groups and can reform or start discussion
// TODO: Replace dummy data with group formation algorithm results from backend

import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import Card from '../../components/Card';
import Button from '../../components/Button';
import { getStaffSocket } from '../../socket';

function GroupFormation() {
  const [groups, setGroups] = useState([]);
  const [students, setStudents] = useState({});
  const [tutorialName, setTutorialName] = useState('');
  const navigate = useNavigate();

  useEffect(() => {
    const socket = getStaffSocket();

    const onUpdate = (tutorial) => {
      if (!tutorial) {
        return;
      }
      setTutorialName(tutorial.name || '');
      setStudents(tutorial.students || {});
      const groupList = Object.entries(tutorial.groups || {}).map(([id, members]) => ({ id, members }));
      setGroups(groupList);

      if (tutorial.state === 'lobby') {
        navigate('/staff/tutorial/' + (tutorial.tutorial_code || ''));
      }
      if (tutorial.state === 'discussion') {
        navigate('/staff/discussion');
      }
    };

    socket.on('tutorial_update', onUpdate);

    return () => {
      socket.off('tutorial_update', onUpdate);
    };
  }, [navigate]);

  const handleReform = () => {
    const socket = getStaffSocket();
    socket.emit('start_grouping');
  };

  const handleBeginDiscussion = () => {
    const socket = getStaffSocket();
    socket.emit('start_discussion');
  };

  const handleResetLobby = () => {
    const socket = getStaffSocket();
    socket.emit('reset_lobby');
  };

  return (
    <div className="container container-lg mt-lg">
      <Card title="Tutorial Session ABCD-1234">
        <div className="card-subtitle">Group Formation Result</div>

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
          <Button variant="outline" onClick={handleReform}>
            Reform Groups
          </Button>
          <Button variant="secondary" onClick={handleBeginDiscussion}>
            Begin Discussion Time
          </Button>
          <Button variant="primary" onClick={handleResetLobby}>
            Back to Lobby
          </Button>
        </div>

      </Card>
    </div>
  );
}

export default GroupFormation;
