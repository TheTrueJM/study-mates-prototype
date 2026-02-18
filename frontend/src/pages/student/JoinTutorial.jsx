// JoinTutorial - Student enters a tutorial code and joins a session

import { useState, useEffect } from 'react';
import Button from '../../components/Button';
import { useNavigate } from 'react-router-dom';
import { getSocket } from '../../socket';

function JoinTutorial() {
  const [code, setCode] = useState('');
  const navigate = useNavigate();

  // useEffect(() => {
  //   const socket = getSocket();

  //   const onTutorialFound = () => {
  //     navigate('/attributes');
  //   };

  //   socket.on("tutorial_found", onTutorialFound);

  //   return () => {
  //     socket.off("tutorial_found", onTutorialFound);
  //   };
  // }, []);

  const handleJoin = async () => {
    if (!code.trim()) return;

    const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || 'http://localhost:5000';

    try {
      const response = await fetch(
        `${BACKEND_URL}/join/${code}`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          credentials: 'include',
        }
      );

      const data = await response.json();

      if (!response.ok) {
        alert(data.error);
        return;
      }
      
      const onTutorialFound = () => {
        navigate('/tutorial');
      };

      const socket = getSocket();

      socket.on("student_update", onTutorialFound);
      socket.emit("join_tutorial", { code });
    } catch (error) {
      console.error("Join tutorial error:", error);
    }
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

export default JoinTutorial;
