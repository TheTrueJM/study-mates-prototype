// GroupFormation - Staff views formed groups and can reform or start discussion
// TODO: Replace dummy data with group formation algorithm results from backend

import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import Card from '../../components/Card';
import Button from '../../components/Button';
import { getStaffSocket } from '../../socket';

function GroupFormation() {
  const [groups, setGroups] = useState([]);
  const [tutorialName, setTutorialName] = useState('');
  const navigate = useNavigate();

  useEffect(() => {
    const socket = getStaffSocket();
    socket.emit('get_update');

    const onUpdate = (tutorial) => {
      console.log("tutorial groups:", tutorial)
      if (!tutorial) return;
      setTutorialName(`${tutorial.name || 'Tutorial'} - ${tutorial.tutorial_code}`);
      const groupList = Object.entries(tutorial.groups || {}).map(([id, members]) => ({ id, members }));
      setGroups(groupList);

      if (tutorial.state === 'lobby') navigate('/staff/tutorial/' + (tutorial.tutorial_code || ''));
      if (tutorial.state === 'discussion') navigate('/staff/discussion');
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

  const handleBackToLobby = () => {
    const socket = getStaffSocket();
    socket.emit('reset_lobby');
  };

  return (
    <div className="container container-lg mt-lg">
      <Card title={tutorialName} actions={(
        <Button variant="outline" onClick={handleBackToLobby}>Back to Lobby</Button>
      )}>
        <div className="card-subtitle">Group Formation Results</div>

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
  );
}

export default GroupFormation;
