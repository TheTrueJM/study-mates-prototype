// JoinSession - Student enters a tutorial code and joins a session

import { useState } from 'react';
import Button from '../../components/Button';

function JoinSession() {
  const [code, setCode] = useState('');
  const [username] = useState('Anonymous-Wombat-42'); // Read-only for now

  const handleJoin = () => {
    console.log('Joining session with code:', code);
    // TODO: Call API -> navigate to /student/attributes
  };

  return (
    <div className="container container-sm mt-lg">
      <div className="card">
        <h1 className="card-header">Join Tutorial Session</h1>

        <div className="flex-col gap-md" style={{ display: 'flex' }}>
          {/* Tutorial code input */}
          <div className="form-group">
            <label className="input-label">Enter Tutorial Code</label>
            <input
              type="text"
              className="input"
              value={code}
              onChange={(e) => setCode(e.target.value)}
              placeholder="ABCD-1234"
            />
          </div>

          {/* Anonymous username display */}
          <div className="form-group">
            <label className="input-label">Your Anonymous Username</label>
            <div className="flex items-center gap-sm">
              <div className="input" style={{ backgroundColor: 'var(--color-gray)', flex: 1 }}>
                {username}
              </div>
              <Button variant="outline">Change</Button>
            </div>
          </div>

          <Button variant="primary" fullWidth onClick={handleJoin}>
            Join Tutorial Session
          </Button>
        </div>
      </div>
    </div>
  );
}

export default JoinSession;
