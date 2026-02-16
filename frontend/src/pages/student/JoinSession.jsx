// JoinSession - Student enters a tutorial code and joins a session

import { useState } from 'react';
import Button from '../../components/Button';
import { useNavigate } from 'react-router-dom';

function JoinSession() {
  const [code, setCode] = useState('');
  const [username] = useState('Anonymous-Wombat-42'); // Read-only for now
  const navigate = useNavigate();

  const handleJoin = () => {
    // Post tutorial code to backend to store in server-side session
    const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || 'http://localhost:5000';
    
    fetch(`${BACKEND_URL}/`, {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: new URLSearchParams({ code }),
      credentials: 'include',
    }).then(() => {
      navigate('/attributes');
    }).catch((err) => console.error(err));
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
              placeholder="ABCDEF..."
            />
          </div>

          <Button variant="primary" fullWidth onClick={handleJoin}>
            Confirm
          </Button>
        </div>
      </div>
    </div>
  );
}

export default JoinSession;
