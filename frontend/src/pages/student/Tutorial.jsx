import { useEffect, useRef, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";

import { useTutorial } from "../../contexts/TutorialContext";
import { ATTRIBUTES } from "../../constants/attributes";

import Card from "../../components/Card";
import Button from "../../components/Button";
import Modal from "../../components/Modal";
import ConfirmDialog from "../../components/ConfirmDialog";
import StudentDetailsForm from "../../components/StudentDetailsForm";

import LobbyLayout from "./LobbyLayout";
import GroupLayout from "./GroupLayout";


function Tutorial() {
  const navigate = useNavigate();
  const { code: rawCode = "" } = useParams();
  const code = rawCode.toUpperCase();

  const {
    sessionReady, studentName, attributes, sharedAttributes, attributesComplete, studentCount,
    tutorialCode, tutorialName, tutorialState, availableAttributes,
    groupNumber, groupMembers, questions, timeRemaining, timeRunning,
    enterTutorial, updateDetails, confirmDetails, leaveTutorial, notify,
  } = useTutorial();

  const [joinAttempt, setJoinAttempt] = useState(0);
  const [joinError, setJoinError] = useState("");
  const [joinPending, setJoinPending] = useState(false);
  const [editing, setEditing] = useState(false);
  const [confirmLeave, setConfirmLeave] = useState(false);
  const [leaving, setLeaving] = useState(false);

  const attemptedJoin = useRef(null);
  const previousAttributes = useRef(null);

  const inSession = tutorialCode === code && !!tutorialState;


  // Keep the URL in a Consistent Format (upper case)
  useEffect(() => {
    if (rawCode !== code) navigate(`/tutorial/${code}`, { replace: true });
  }, [rawCode, code, navigate]);

  // Join the Tutorial in the URL once connected (re-joining a tutorial the student is already in just resumes it)
  useEffect(() => {
    const attemptKey = `${code}:${joinAttempt}`;
    if (!sessionReady || tutorialCode === code || attemptedJoin.current === attemptKey) return;
    attemptedJoin.current = attemptKey;

    setJoinPending(true);
    enterTutorial(code).then((response) => {
      setJoinPending(false);
      if (!response.ok) setJoinError(response.message || "Unable to join this session.");
    });
  }, [sessionReady, tutorialCode, code, joinAttempt, enterTutorial]);

  // Let Students know when their Tutor asks for Additional Details Mid-Session
  const attributesKey = availableAttributes.join(",");
  useEffect(() => {
    if (!inSession) return;
    const previous = previousAttributes.current;
    previousAttributes.current = attributesKey;
    if (previous === null || !attributesComplete) return;

    const added = attributesKey.split(",").filter((a) => a && !previous.split(",").includes(a));
    if (added.length) {
      const labels = added.map((a) => ATTRIBUTES[a]?.label.toLowerCase() ?? a).join(", ");
      notify(`Your Tutor has asked for More Details (${labels}). Use "Edit my Details" to add them.`, "info", 8000);
    }
  }, [attributesKey, inSession, attributesComplete, notify]);


  const handleDone = async () => {
    const response = await confirmDetails();
    if (response.ok) setEditing(false);
  };

  const handleLeave = async () => {
    setLeaving(true);
    const response = await leaveTutorial();
    setLeaving(false);
    if (response.ok) {
      setConfirmLeave(false);
      notify("You Left the Session.", "info");
    }
  };

  const retryJoin = () => {
    setJoinError("");
    setJoinAttempt((attempt) => attempt + 1);
  };


  if (joinError) {
    return (
      <div className="container container-sm page">
        <Card title="Couldn't join session">
          <p className="mb-md">{joinError}</p>
          <div className="btn-group">
            <Link to="/" className="btn btn-outline">Enter a Different Code</Link>
            <Button onClick={retryJoin}>Try Again</Button>
          </div>
        </Card>
      </div>
    );
  }

  // Previously Joined, but no longer in the Session (e.g. the server restarted)
  if (!inSession && sessionReady && !joinPending && attemptedJoin.current === `${code}:${joinAttempt}`) {
    return (
      <div className="container container-sm page">
        <Card title="You're no longer in this Session">
          <p className="mb-md">Your Connection to Session {code} was Reset.</p>
          <div className="btn-group">
            <Link to="/" className="btn btn-outline">Back to Home</Link>
            <Button onClick={retryJoin}>Rejoin Session</Button>
          </div>
        </Card>
      </div>
    );
  }

  if (!inSession) {
    return (
      <div className="container container-sm page">
        <div className="card text-center">
          <div className="loading-dots mb-sm" aria-hidden="true">
            <div className="dot" />
            <div className="dot" />
            <div className="dot" />
          </div>
          <p>Joining Session {code}…</p>
        </div>
      </div>
    );
  }

  const inLobby = tutorialState === "lobby";

  return (
    <div className="container container-md page">
      <Card
        title={tutorialName}
        subtitle={<>Session Code <strong className="code-inline">{code}</strong></>}
        actions={<Button variant="outline" size="sm" onClick={() => setConfirmLeave(true)}>Leave</Button>}
      >
        {inLobby ? (
          <LobbyLayout
            username={studentName}
            studentCount={studentCount}
            attributes={attributes}
            sharedAttributes={sharedAttributes}
            attributesComplete={attributesComplete}
            availableAttributes={availableAttributes}
            editing={!attributesComplete || editing}
            onEdit={() => setEditing(true)}
            onSave={updateDetails}
            onDone={handleDone}
          />
        ) : (
          <GroupLayout
            state={tutorialState}
            username={studentName}
            groupNumber={groupNumber}
            groupMembers={groupMembers}
            attributes={attributes}
            availableAttributes={availableAttributes}
            attributesComplete={attributesComplete}
            questions={questions}
            timeRemaining={timeRemaining}
            timeRunning={timeRunning}
            onEdit={() => setEditing(true)}
          />
        )}
      </Card>

      {/* Editing details during group rounds */}
      <Modal title="Your details" isOpen={editing && !inLobby} onClose={() => setEditing(false)}>
        <p className="text-muted mb-md">
          Changes save automatically and your Group sees them straight away. Everything is Optional.
        </p>
        <StudentDetailsForm
          availableAttributes={availableAttributes}
          initialAttributes={attributes}
          initialShared={sharedAttributes}
          onSave={updateDetails}
          onDone={handleDone}
          doneLabel="Done"
        />
      </Modal>

      <ConfirmDialog
        isOpen={confirmLeave}
        title="Leave this Session?"
        message="Your Details will be removed and you'll leave your Group. You can Rejoin with the Code, but you'll get a New Name."
        confirmLabel="Leave Session"
        danger
        busy={leaving}
        onConfirm={handleLeave}
        onCancel={() => setConfirmLeave(false)}
      />
    </div>
  );
}

export default Tutorial;
