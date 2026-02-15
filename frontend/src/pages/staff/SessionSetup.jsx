// SessionSetup - Staff configures group size and discussion time before starting

import { useState } from 'react';
import Card from '../../components/Card';
import Input from '../../components/Input';
import Button from '../../components/Button';

function SessionSetup() {
  const [membersPerGroup, setMembersPerGroup] = useState(4);
  const [discussionTime, setDiscussionTime] = useState('10');

  const handleBegin = () => {
    console.log('Session setup:', { membersPerGroup, discussionTime });
    // TODO: Call API -> navigate to /staff/lobby
  };

  return (
    <div className="container container-md mt-lg">
      <Card title="Tutorial Session Setup">

        {/* Members per group slider (range: 2-8) */}
        <div className="form-group">
          <label className="input-label">Members per Group</label>
          <div className="range-group">
            <input
              type="range"
              min="2"
              max="8"
              value={membersPerGroup}
              onChange={(e) => setMembersPerGroup(Number(e.target.value))}
            />
            <div className="range-value">{membersPerGroup}</div>
          </div>
          <div className="range-labels">
            <span>2</span>
            <span>8</span>
          </div>
        </div>

        {/* Discussion time input */}
        <Input
          label="Round Discussion Time (minutes)"
          type="number"
          value={discussionTime}
          onChange={setDiscussionTime}
          placeholder="e.g. 10"
        />

        <div className="mt-md">
          <Button variant="secondary" fullWidth onClick={handleBegin}>
            Begin Tutorial Session
          </Button>
        </div>

      </Card>
    </div>
  );
}

export default SessionSetup;
