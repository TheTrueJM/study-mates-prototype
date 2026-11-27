import { useEffect, useRef, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";

import { useTutorial } from "../../contexts/TutorialContext";

import Card from "../../components/Card";
import Button from "../../components/Button";
import Modal from "../../components/Modal";
import ConfirmDialog from "../../components/ConfirmDialog";
import TutorialSettingsFields from "../../components/TutorialSettingsFields";
import { validateSettings } from "../../constants/settings";

import LobbyLayout from "./LobbyLayout";
import GroupsLayout from "./GroupsLayout";
import DiscussionLayout from "./DiscussionLayout";
import WrapUpLayout from "./WrapUpLayout";


function Tutorial() {
  const navigate = useNavigate();
  const { code } = useParams();

  const {
    sessionReady, tutorialCode, tutorialName, tutorialState, locked, groupSize, maxGroups, availableAttributes,
    students, groups, round, questions, discussionTime, timeDuration, timeRemaining, timeRunning, timeEndsAt,
    updateTutorial, lockTutorial, removeStudent, backToLobby, startGrouping, startDiscussion, skipIntroduction, wrapUp, endTutorial,
    startTimer, stopTimer, resetTimer, adjustTimer, notify,
  } = useTutorial();

  const [settingsValues, setSettingsValues] = useState(null);
  const [settingsErrors, setSettingsErrors] = useState({});
  const [savingSettings, setSavingSettings] = useState(false);
  const [confirmEnd, setConfirmEnd] = useState(false); // Ending the Tutorial (Wrapping Up)
  const [confirmClose, setConfirmClose] = useState(false); // Closing the Session
  const [ending, setEnding] = useState(false);
  const [removing, setRemoving] = useState(null); // Student ID
  const [removeBusy, setRemoveBusy] = useState(false);
  const [busy, setBusy] = useState("");

  const wasRunning = useRef(false);


  // Once the Session is Known, redirect if this isn't the Staff Member's Running Tutorial
  useEffect(() => {
    if (!sessionReady) return;
    if (!tutorialCode) {
      // Otherwise it was running when this page opened, so why it has Closed is already notified
      if (!wasRunning.current) notify(`Session ${code} is no longer Running.`, "info", 8000);
      wasRunning.current = true;
      navigate("/staff/", { replace: true });
    } else {
      wasRunning.current = true;
      if (tutorialCode !== code) navigate(`/staff/tutorial/${tutorialCode}`, { replace: true });
    }
  }, [sessionReady, tutorialCode, code, navigate, notify]);


  // Errors are Reported by the Server as Notifications
  const run = (key, action) => async () => {
    setBusy(key);
    await action();
    setBusy("");
  };

  const openSettings = () => {
    setSettingsErrors({});
    setSettingsValues({
      groupSize: groupSize ?? 5,
      limitGroups: !!maxGroups,
      maxGroups: maxGroups ?? "",
      discussionTime: discussionTime ? Math.round((discussionTime / 60) * 100) / 100 : 5,
      availableAttributes: [...availableAttributes],
    });
  };

  const handleSaveSettings = async () => {
    const { settings, errors } = validateSettings(settingsValues);
    setSettingsErrors(errors);
    if (Object.keys(errors).length) return;

    setSavingSettings(true);
    const response = await updateTutorial(settings);
    setSavingSettings(false);

    if (response.ok) {
      setSettingsValues(null);
      notify("Settings Updated.", "success");
    }
  };

  const handleEnd = async () => {
    setEnding(true);
    await wrapUp();
    setEnding(false);
    setConfirmEnd(false);
  };

  const handleClose = async () => {
    setEnding(true);
    await endTutorial();
    setEnding(false);
    setConfirmClose(false);
  };

  const handleRemove = async () => {
    setRemoveBusy(true);
    await removeStudent(removing);
    setRemoveBusy(false);
    setRemoving(null);
  };


  if (!tutorialState || tutorialCode !== code) {
    return (
      <div className="container container-sm page">
        <div className="card text-center">
          <div className="loading-dots mb-sm" aria-hidden="true">
            <div className="dot" />
            <div className="dot" />
            <div className="dot" />
          </div>
          <p>Loading Session…</p>
        </div>
      </div>
    );
  }

  const studentCount = Object.keys(students).length;
  const inLobby = tutorialState === "lobby";
  const wrappingUp = tutorialState === "wrap_up";
  const timer = { timeRemaining, timeDuration, timeRunning, timeEndsAt, onStart: startTimer, onStop: stopTimer, onAdjust: adjustTimer };

  // Before any Groups have Met there is nothing to Wrap Up, so the Session just Closes
  const endSession = () => (round > 0 && !wrappingUp ? setConfirmEnd(true) : setConfirmClose(true));

  return (
    <div className="container container-lg page">
      <Card
        title={tutorialName}
        subtitle={
          <>
            Code <strong className="code-inline">{code}</strong>
            {locked && " (Locked)"} · {studentCount} Student{studentCount === 1 ? "" : "s"}
            {round > 0 && !inLobby && <> · <strong>Round {round}</strong></>}
          </>
        }
        actions={
          <>
            {!inLobby && (
              <Button variant="outline" size="sm" onClick={run("lobby", backToLobby)} disabled={!!busy}>
                Back to Lobby
              </Button>
            )}
            <Button variant="outline" size="sm" onClick={() => lockTutorial(!locked)} aria-pressed={locked}>
              {locked ? "Unlock Joining" : "Lock Joining"}
            </Button>
            <Button variant="outline" size="sm" onClick={openSettings}>Settings</Button>
            <Button variant="danger" size="sm" onClick={endSession}>{wrappingUp ? "Close Session" : "End Session"}</Button>
          </>
        }
      >
        {inLobby && (
          <LobbyLayout
            code={code}
            locked={locked}
            students={students}
            availableAttributes={availableAttributes}
            onRemoveStudent={setRemoving}
            onGrouping={run("grouping", startGrouping)}
            busy={busy === "grouping"}
          />
        )}
        {tutorialState === "grouping" && (
          <GroupsLayout
            students={students}
            groups={groups}
            onGrouping={run("grouping", startGrouping)}
            onDiscussion={run("discussion", startDiscussion)}
            onRemoveStudent={setRemoving}
            busy={busy}
          />
        )}
        {(tutorialState === "introduction" || tutorialState === "discussion") && (
          <DiscussionLayout
            introduction={tutorialState === "introduction"}
            questions={questions}
            timer={timer}
            students={students}
            groups={groups}
            onGrouping={run("grouping", startGrouping)}
            onResetTimer={() => resetTimer()}
            onSkipIntroduction={run("skip", skipIntroduction)}
            onRemoveStudent={setRemoving}
            busy={busy}
          />
        )}
        {wrappingUp && (
          <WrapUpLayout
            timer={timer}
            round={round}
            studentCount={studentCount}
            onResetTimer={() => resetTimer()}
            onClose={() => setConfirmClose(true)}
          />
        )}
      </Card>


      <Modal
        title="Session Settings"
        isOpen={!!settingsValues}
        onClose={() => setSettingsValues(null)}
        footer={
          <div className="btn-group">
            <Button variant="outline" onClick={() => setSettingsValues(null)}>Cancel</Button>
            <Button variant="primary" onClick={handleSaveSettings} disabled={savingSettings}>
              {savingSettings ? "Saving…" : "Save Settings"}
            </Button>
          </div>
        }
      >
        {settingsValues && (
          <>
            <TutorialSettingsFields
              values={settingsValues}
              onChange={(values) => {
                setSettingsValues(values);
                setSettingsErrors({});
              }}
              errors={settingsErrors}
            />
            <p className="input-hint">
              Group Settings apply from the Next Grouping Round. Changes to Student Details update Students' Forms straight away.
            </p>
          </>
        )}
      </Modal>

      <ConfirmDialog
        isOpen={confirmEnd}
        title="End the Tutorial?"
        message="Everyone will see a Wrap-Up Screen with time to Return to their Seats. You can Close the Session afterwards."
        confirmLabel="End Tutorial"
        busy={ending}
        onConfirm={handleEnd}
        onCancel={() => setConfirmEnd(false)}
      />

      <ConfirmDialog
        isOpen={confirmClose}
        title="Close this Session?"
        message="All Students will be Removed and their Details Deleted. This can't be Undone."
        confirmLabel="Close Session"
        danger
        busy={ending}
        onConfirm={handleClose}
        onCancel={() => setConfirmClose(false)}
      />

      <ConfirmDialog
        isOpen={!!removing}
        title={`Remove ${students[removing]?.name ?? "this Student"}?`}
        message="Their Details will be Deleted and they'll leave their Group. They can Rejoin with the Code unless Joining is Locked."
        confirmLabel="Remove Student"
        danger
        busy={removeBusy}
        onConfirm={handleRemove}
        onCancel={() => setRemoving(null)}
      />
    </div>
  );
}

export default Tutorial;
