// JoinTutorial - Student enters a tutorial code and joins a session

import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import Button from '../../components/Button';
import { useAuth } from '../../hooks/useAuth';
import { getSocket } from '../../socket';

function JoinTutorial() {
  const [socketInstance, setSocketInstance] = useState(null);
  const [code, setCode] = useState('');
  const navigate = useNavigate();
  const { studentDetails, setStudent } = useAuth();

  useEffect(() => {
    const socket = getSocket();
    setSocketInstance(socket);

    const onTutorialFound = (tutorial) => {
      navigate(`/tutorial/${tutorial.tutorial_code}`);
    };

    socket.on("student_update", onTutorialFound);

    return () => {
      socket.off("student_update", onTutorialFound);
    };
  }, []);

  const handleJoin = async () => {
    if (!code.trim()) {
      alert("Please enter a tutorial code.");
      return;
    }

    try {
      // Update frontend state with tutorial code
      setStudent({
        ...studentDetails,
        code: code.trim().toUpperCase()
      });

      const onError = (err) => {
        alert(err.message || "An error occurred while joining the tutorial.");
        socketInstance.off("error", onError);
      };

      socketInstance.emit("join_tutorial", { code: code.trim().toUpperCase(), details: studentDetails });
      socketInstance.on("error", onError);
    } catch (err) {
      alert(err.message);
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
