import { useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";

import { useTutorial } from "../../contexts/TutorialContext";
import { loadResults } from "../../results";

import Card from "../../components/Card";
import Button from "../../components/Button";
import TextInput from "../../components/TextInput";


const CODE_LENGTH = 6;
const cleanCode = (value = "") => value.toUpperCase().replace(/[^A-Z0-9]/g, "").slice(0, CODE_LENGTH);


function JoinTutorial() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();

  const { enterTutorial, tutorialCode, tutorialName } = useTutorial();

  const [code, setCode] = useState(() => cleanCode(searchParams.get("code") || ""));
  const [error, setError] = useState("");
  const [joining, setJoining] = useState(false);
  const [pastSessions] = useState(() => loadResults().length);


  const handleJoin = async (event) => {
    event.preventDefault();

    if (!code) {
      setError("Enter the Code shown on your Tutor's Screen.");
      return;
    }

    setJoining(true);
    setError("");
    const response = await enterTutorial(code);
    setJoining(false);

    if (response.ok) {
      navigate(`/tutorial/${response.tutorial_code}`);
    } else {
      setError(response.message || "Unable to Join this Session.");
    }
  };


  return (
    <div className="container container-sm page">
      {tutorialCode && (
        <div className="callout mb-md">
          <p>You're Still In <strong>{tutorialName || tutorialCode}</strong>.</p>
          <Link to={`/tutorial/${tutorialCode}`} className="btn btn-primary btn-sm">Return to Session</Link>
        </div>
      )}

      <Card title="Join a Tutorial Session">
        <p className="text-muted mb-md">
          Enter the Code shown on your Tutor's Screen. You'll get a Random Anonymous Name, so no Personal Details are required.
        </p>

        <form onSubmit={handleJoin} noValidate>
          <div className="code-input">
            <TextInput
              name="tutorial-code"
              label="Tutorial code"
              value={code}
              onChange={(value) => {
                setCode(cleanCode(value));
                setError("");
              }}
              placeholder="ABCDEF"
              error={error}
              autoComplete="off"
              autoCapitalize="characters"
              autoCorrect="off"
              spellCheck={false}
              enterKeyHint="go"
            />
          </div>

          <Button type="submit" variant="primary" fullWidth disabled={joining}>
            {joining ? "Joining…" : "Join Session"}
          </Button>
        </form>

        {pastSessions > 0 && (
          <Button variant="subtle" size="sm" fullWidth className="mt-sm" onClick={() => navigate("/results")}>
            Your Past Sessions ({pastSessions})
          </Button>
        )}
      </Card>
    </div>
  );
}

export default JoinTutorial;
