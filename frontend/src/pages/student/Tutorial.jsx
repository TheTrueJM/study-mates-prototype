import { useEffect, useRef, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";

import { useTutorial } from "../../contexts/TutorialContext";
import { useAttributeCatalog } from "../../hooks/useAttributeCatalog";

import Card from "../../components/Card";
import Button from "../../components/Button";
import Modal from "../../components/Modal";
import ConfirmDialog from "../../components/ConfirmDialog";
import StudentDetailsForm from "../../components/StudentDetailsForm";

import LobbyLayout from "./LobbyLayout";
import GroupLayout from "./GroupLayout";
import WrapUpLayout from "./WrapUpLayout";


function Tutorial() {
  const navigate = useNavigate();
  const { code: rawCode = "" } = useParams();
  const code = rawCode.toUpperCase();

  const {
    sessionReady, studentName, attributes, sharedAttributes, attributesComplete, studentCount,
    tutorialCode, tutorialName, tutorialState, availableAttributes,
    round, formation, groupNumber, groupMembers, questions, timeRemaining, timeRunning, timeEndsAt, history, shortlisting,
    enterTutorial, updateDetails, confirmDetails, leaveTutorial, shortlistStudent, notify,
  } = useTutorial();

  const catalog = useAttributeCatalog();
  const [joinAttempt, setJoinAttempt] = useState(0);
  const [joinError, setJoinError] = useState("");
  const [joinPending, setJoinPending] = useState(false);
  const [editing, setEditing] = useState(false);
  const [confirmLeave, setConfirmLeave] = useState(false);
  const [leaving, setLeaving] = useState(false);

  const attemptedJoin = useRef(null);
  const previousAttributes = useRef(null);
  const previousFormation = useRef(null);

  const inSession = tutorialCode === code && !!tutorialState;


  // Keep the URL in a Consistent Format (upper case)
  useEffect(() => {
    if (rawCode !== code) navigate(`/tutorial/${code}`, { replace: true });
  }, [rawCode, code, navigate]);

  // Join the Tutorial in the URL once connected (re-joining a tutorial the student is already in just resumes it)
  useEffect(() => {
    const attemptKey = `${code}:${joinAttempt}`;
    if (!sessionReady || attemptedJoin.current === attemptKey) return;
    attemptedJoin.current = attemptKey;

    // Already being in the Tutorial counts as an attempt, so that no longer being in it doesn't join it again
    if (tutorialCode === code) return;

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
      const labels = added.map((a) => catalog.meta[a]?.label ?? a).join(", ");
      notify(`Your Tutor has asked for More Details (${labels}). Use "Edit my Details" to add them.`, "info", 8000);
    }
  }, [attributesKey, inSession, attributesComplete, notify, catalog]);

  // Stop Editing Details when New Groups are formed, so that the Student sees their Group
  // (closing the form saves any Unsaved Change)
  useEffect(() => {
    if (!inSession) return;
    const previous = previousFormation.current;
    previousFormation.current = formation;
    if (previous === null || previous === formation || !editing) return;

    setEditing(false);
    notify("New Groups have been Formed. Any Changes to your Details were Saved.", "info", 8000);
  }, [formation, inSession, editing, notify]);


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
            history={history}
            shortlisting={shortlisting}
            onShortlist={shortlistStudent}
          />
        ) : tutorialState === "wrap_up" ? (
          <WrapUpLayout
            timeRemaining={timeRemaining}
            timeRunning={timeRunning}
            timeEndsAt={timeEndsAt}
            history={history}
            shortlisting={shortlisting}
            onShortlist={shortlistStudent}
          />
        ) : (
          <GroupLayout
            state={tutorialState}
            username={studentName}
            round={round}
            groupNumber={groupNumber}
            groupMembers={groupMembers}
            attributes={attributes}
            availableAttributes={availableAttributes}
            attributesComplete={attributesComplete}
            questions={questions}
            timeRemaining={timeRemaining}
            timeRunning={timeRunning}
            timeEndsAt={timeEndsAt}
            onEdit={() => setEditing(true)}
            history={history}
            shortlisting={shortlisting}
            onShortlist={shortlistStudent}
          />
        )}
      </Card>

      {/* Editing details during group rounds */}
      <Modal title="Your Details" isOpen={editing && !inLobby} onClose={() => setEditing(false)}>
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
