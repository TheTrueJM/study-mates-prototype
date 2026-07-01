import { useState } from "react";
import { useNavigate } from "react-router-dom";

import { useTutorial } from "../../contexts/TutorialContext";

import Button from "../../components/Button";

function JoinTutorial() {
  const navigate = useNavigate();

  const { enterTutorial } = useTutorial();

  const [code, setCode] = useState("");


  const handleJoin = (e) => {
    e.preventDefault();
    enterTutorial(code);
  }

  // TODO: Handle Socket Errors (e.g. Invalid Tutorial Code)


  return (
    <div className="container container-sm mt-lg">
      <div className="card">
        <h1 className="card-header">Join Tutorial Session</h1>

        <div className="flex-col gap-md" style={{ display: "flex" }}>
          {/* Tutorial Code Input */}
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
