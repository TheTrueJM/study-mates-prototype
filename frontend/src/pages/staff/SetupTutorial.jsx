import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import { useTutorial } from "../../contexts/TutorialContext";
import { DEFAULT_AVAILABLE_ATTRIBUTES } from "../../constants/attributes";

import Card from "../../components/Card";
import Button from "../../components/Button";
import TextInput from "../../components/TextInput";
import ConfirmDialog from "../../components/ConfirmDialog";
import TutorialSettingsFields from "../../components/TutorialSettingsFields";
import { validateSettings } from "../../constants/settings";


function TutorialSetup() {
  const navigate = useNavigate();
  const { tutorialCode, tutorialName, createTutorial, endTutorial } = useTutorial();

  const [name, setName] = useState("");
  const [settings, setSettings] = useState({
    groupSize: 5,
    limitGroups: false,
    maxGroups: "",
    discussionTime: 5,
    availableAttributes: [...DEFAULT_AVAILABLE_ATTRIBUTES],
  });
  const [errors, setErrors] = useState({});
  const [formError, setFormError] = useState("");
  const [creating, setCreating] = useState(false);
  const [confirmEnd, setConfirmEnd] = useState(false);
  const [ending, setEnding] = useState(false);


  const handleBegin = async (event) => {
    event.preventDefault();
    setFormError("");

    const { settings: validated, errors: validationErrors } = validateSettings(settings);
    setErrors(validationErrors);
    if (Object.keys(validationErrors).length) return;

    setCreating(true);
    const response = await createTutorial({ tutorial_name: name.trim(), ...validated });
    setCreating(false);

    if (response.ok) {
      navigate(`/staff/tutorial/${response.tutorial_code}`);
    } else {
      setFormError(response.message || "The Session couldn't be Created.");
    }
  };

  const handleEnd = async () => {
    setEnding(true);
    await endTutorial();
    setEnding(false);
    setConfirmEnd(false);
  };


  return (
    <div className="container container-md page">
      {tutorialCode && (
        <div className="callout mb-md">
          <p>You have a Session in Progress: <strong>{tutorialName || tutorialCode}</strong>.</p>
          <div className="callout-actions">
            <Button variant="danger" size="sm" onClick={() => setConfirmEnd(true)}>End It</Button>
            <Link to={`/staff/tutorial/${tutorialCode}`} className="btn btn-primary btn-sm">Resume Session</Link>
          </div>
        </div>
      )}

      <Card title="Start a Tutorial Session">
        <form onSubmit={handleBegin} noValidate>
          <TextInput
            name="name"
            label="Session Name (optional)"
            value={name}
            placeholder="e.g. Tutorial 3, Wednesday 10am"
            onChange={setName}
            maxLength={60}
          />

          <TutorialSettingsFields
            values={settings}
            onChange={(values) => {
              setSettings(values);
              setErrors({});
            }}
            errors={errors}
          />

          {formError && <p className="input-error mb-sm" role="alert">{formError}</p>}

          <Button type="submit" variant="secondary" fullWidth disabled={creating || !!tutorialCode}>
            {creating ? "Starting…" : "Begin Tutorial Session"}
          </Button>
          {tutorialCode && (
            <p className="input-hint mt-xs text-center">End or Resume your Current Session to Start a New One.</p>
          )}
        </form>
      </Card>

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

export default TutorialSetup;
