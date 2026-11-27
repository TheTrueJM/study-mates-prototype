import { useEffect, useMemo, useRef, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";

import { useTutorial } from "../../contexts/TutorialContext";

import Card from "../../components/Card";
import Button from "../../components/Button";
import Modal from "../../components/Modal";
import ConfirmDialog from "../../components/ConfirmDialog";
import TutorialSettingsFields from "../../components/TutorialSettingsFields";
import { validateSettings, SEAT_FLASH_DURATION } from "../../constants/settings";
import { isCustomAttribute } from "../../constants/attributes";

import LobbyLayout from "./LobbyLayout";
import GroupsLayout from "./GroupsLayout";
import DiscussionLayout from "./DiscussionLayout";
import WrapUpLayout from "./WrapUpLayout";



function Tutorial() {
  const navigate = useNavigate();
  const { code } = useParams();

  const {
    sessionReady, tutorialCode, tutorialName, tutorialState, locked, groupSize, maxGroups, availableAttributes, customAttributes, shortlisting, mutualPairs,
    seating, tableNumbering,
    students, groups, round, questions, discussionTime, timeDuration, timeRemaining, timeRunning, timeEndsAt,
    updateTutorial, lockTutorial, removeStudent, moveStudent, backToLobby, startGrouping, startDiscussion, skipIntroduction, wrapUp, endTutorial,
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
  const [seatFlashes, setSeatFlashes] = useState({}); // { Student ID: Table }

  const wasRunning = useRef(false);
  const previousSeats = useRef(null);
  const flashTimers = useRef([]);


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


  // Students staying at their Table (only when Seating Needs are on)
  const seats = useMemo(() => Object.fromEntries(Object.entries(students).map(([id, student]) => [id, {
    table: seating && student.stay_seated ? (student.table ?? null) : null,
    needsTable: seating && !!student.needs_table,
  }])), [students, seating]);
  const needsTableCount = Object.values(seats).filter((seat) => seat.needsTable).length;

  // A Table a Student has just set is briefly shown beside their Name, and Staff are told (without saying who)
  // when someone needs the Table Numbers. Nothing is shown for Students already Seated when the page opens.
  useEffect(() => {
    const previous = previousSeats.current;
    previousSeats.current = seats;
    if (!previous) return;

    const set = Object.entries(seats).filter(([id, seat]) => seat.table !== null && seat.table !== previous[id]?.table);
    if (set.length) {
      setSeatFlashes((current) => ({ ...current, ...Object.fromEntries(set.map(([id, seat]) => [id, seat.table])) }));
      flashTimers.current.push(setTimeout(() => setSeatFlashes((current) => {
        const next = { ...current };
        set.forEach(([id, seat]) => next[id] === seat.table && delete next[id]);
        return next;
      }), SEAT_FLASH_DURATION));
    }

    const asking = Object.entries(seats).filter(([id, seat]) => seat.needsTable && !previous[id]?.needsTable).length;
    if (asking) notify(asking === 1 ? "A Student needs the Table Numbers." : `${asking} Students need the Table Numbers.`, "info", 8000);
  }, [seats, notify]);

  useEffect(() => () => flashTimers.current.forEach(clearTimeout), []);

  const displayStudents = useMemo(() => Object.fromEntries(Object.entries(students).map(([id, student]) => [id, {
    ...student,
    seatTable: seats[id]?.table ?? null,
    needsTable: !!seats[id]?.needsTable,
    flash: seatFlashes[id] !== undefined && seatFlashes[id] === seats[id]?.table,
  }])), [students, seats, seatFlashes]);


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
      availableAttributes: availableAttributes.filter((attribute) => !isCustomAttribute(attribute)),
      customAttributes: customAttributes.map((detail) => ({ ...detail, options: [...detail.options] })),
      shortlisting,
      seating,
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
        {needsTableCount > 0 && !wrappingUp && (
          <div className="seating-note mb-md" role="status">
            <p>
              <strong>{needsTableCount === 1 ? "A Student needs" : `${needsTableCount} Students need`} the Table Numbers.</strong>{" "}
              Let the Class know how the Tables are Numbered or show a Seating Plan so they can enter theirs.
            </p>
          </div>
        )}

        {inLobby && (
          <LobbyLayout
            code={code}
            locked={locked}
            students={displayStudents}
            availableAttributes={availableAttributes}
            onRemoveStudent={setRemoving}
            onGrouping={run("grouping", startGrouping)}
            busy={busy === "grouping"}
          />
        )}
        {tutorialState === "grouping" && (
          <GroupsLayout
            students={displayStudents}
            groups={groups}
            maxGroups={maxGroups}
            tableNumbering={seating && tableNumbering}
            onMoveStudent={moveStudent}
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
            students={displayStudents}
            groups={groups}
            maxGroups={maxGroups}
            onMoveStudent={moveStudent}
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
            shortlisting={shortlisting}
            mutualPairs={mutualPairs}
            onResetTimer={() => resetTimer()}
            onClose={() => setConfirmClose(true)}
          />
        )}
      </Card>


      <Modal
        title="Session Settings"
        size="lg"
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
