import { useEffect, useState } from "react";
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


function Tutorial() {
  const navigate = useNavigate();
  const { code } = useParams();

  const {
    sessionReady, tutorialCode, tutorialName, tutorialState, groupSize, maxGroups, availableAttributes,
    students, groups, questions, timeDuration, timeRemaining, timeRunning,
    updateTutorial, backToLobby, startGrouping, startDiscussion, endTutorial,
    startTimer, stopTimer, resetTimer, notify,
  } = useTutorial();

  const [settingsValues, setSettingsValues] = useState(null);
  const [settingsErrors, setSettingsErrors] = useState({});
  const [savingSettings, setSavingSettings] = useState(false);
  const [confirmEnd, setConfirmEnd] = useState(false);
  const [ending, setEnding] = useState(false);
  const [busy, setBusy] = useState("");


  // Once the Session is Known, redirect if this isn't the Staff Member's Running Tutorial
  useEffect(() => {
    if (!sessionReady) return;
    if (!tutorialCode) {
      navigate("/staff/", { replace: true });
    } else if (tutorialCode !== code) {
      navigate(`/staff/tutorial/${tutorialCode}`, { replace: true });
    }
  }, [sessionReady, tutorialCode, code, navigate]);


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
      discussionTime: timeDuration ? Math.round((timeDuration / 60) * 100) / 100 : 5,
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
    await endTutorial();
    setEnding(false);
    setConfirmEnd(false);
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

  return (
    <div className="container container-lg page">
      <Card
        title={tutorialName}
        subtitle={<>Code <strong className="code-inline">{code}</strong> · {studentCount} Student{studentCount === 1 ? "" : "s"}</>}
        actions={
          <>
            {tutorialState !== "lobby" && (
              <Button variant="outline" size="sm" onClick={run("lobby", backToLobby)} disabled={!!busy}>
                Back to Lobby
              </Button>
            )}
            <Button variant="outline" size="sm" onClick={openSettings}>Settings</Button>
            <Button variant="danger" size="sm" onClick={() => setConfirmEnd(true)}>End Session</Button>
          </>
        }
      >
        {tutorialState === "lobby" && (
          <LobbyLayout
            code={code}
            students={students}
            availableAttributes={availableAttributes}
            onGrouping={run("grouping", startGrouping)}
            busy={busy === "grouping"}
          />
        )}
        {(tutorialState === "grouping" || tutorialState === "introduction") && (
          <GroupsLayout
            students={students}
            groups={groups}
            onGrouping={run("grouping", startGrouping)}
            onDiscussion={run("discussion", startDiscussion)}
            busy={busy}
          />
        )}
        {tutorialState === "discussion" && (
          <DiscussionLayout
            questions={questions}
            timeRemaining={timeRemaining}
            timeDuration={timeDuration}
            timeRunning={timeRunning}
            students={students}
            groups={groups}
            onGrouping={run("grouping", startGrouping)}
            onStartTimer={startTimer}
            onStopTimer={stopTimer}
            onResetTimer={() => resetTimer()}
            busy={busy}
          />
        )}
      </Card>


      <Modal
        title="Session settings"
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
        title="End this Session?"
        message="All Students will be Removed and their Details Deleted. This can't be Undone."
        confirmLabel="End Session"
        danger
        busy={ending}
        onConfirm={handleEnd}
        onCancel={() => setConfirmEnd(false)}
      />
    </div>
  );
}

export default Tutorial;
