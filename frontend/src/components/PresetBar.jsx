import { useEffect, useState } from "react";

import { useAuth } from "../contexts/AuthContext";
import { matchesSettings, settingsToValues, validateSettings } from "../constants/settings";

import Button from "./Button";


const MAX_NAME_LENGTH = 50; // Mirrors MAX_PRESET_NAME_LENGTH in backend/app/routes/saved.py


/**
 * Settings Presets saved to a Staff Account: Load one to fill in the Settings, Update it with the
 * Current Settings, or Save the Current Settings as a New Preset.
 */
export default function PresetBar({ values, onChange }) {
  const { isAccount, request } = useAuth();

  const [presets, setPresets] = useState(null);
  const [loadedId, setLoadedId] = useState(null);
  const [naming, setNaming] = useState(false);
  const [name, setName] = useState("");
  const [replaceId, setReplaceId] = useState(null); // A Preset with the same Name, which can be Replaced
  const [confirmDelete, setConfirmDelete] = useState(false);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState(null); // { text, error }

  useEffect(() => {
    if (!isAccount) return undefined;
    let cancelled = false;
    request("/presets").then((response) => {
      if (cancelled) return;
      if (response.ok) setPresets(response.data.presets || []);
      else setMessage({ text: response.message, error: true });
    });
    return () => {
      cancelled = true;
    };
  }, [isAccount, request]);

  if (!isAccount) {
    return <p className="input-hint preset-hint">Sign in with a Staff Account to Save these Settings as a Preset.</p>;
  }

  const loaded = presets?.find((preset) => preset.id === loadedId);
  const changed = loaded && !matchesSettings(values, loaded.settings);

  const keep = (preset) => {
    setPresets((current) => [...current.filter((p) => p.id !== preset.id), preset].sort((a, b) => a.name.localeCompare(b.name)));
    setLoadedId(preset.id);
  };

  // The Current Settings, or null (with a Message) if they aren't Valid
  const currentSettings = () => {
    const { settings, errors } = validateSettings(values);
    if (Object.keys(errors).length) {
      setMessage({ text: "Fix the Settings below before Saving them.", error: true });
      return null;
    }
    return settings;
  };

  const load = (id) => {
    setMessage(null);
    setConfirmDelete(false);
    const preset = presets.find((p) => p.id === Number(id));
    setLoadedId(preset?.id ?? null);
    if (preset) onChange(settingsToValues(preset.settings));
  };

  const save = async (path, method, body, done) => {
    setBusy(true);
    const response = await request(path, { method, body });
    setBusy(false);

    if (response.ok) {
      keep(response.data.preset);
      setMessage({ text: done });
      setNaming(false);
      setReplaceId(null);
    } else {
      setMessage({ text: response.message, error: true });
      if (response.status === 409) setReplaceId(response.data.preset_id ?? null);
    }
  };

  const saveNew = () => {
    const settings = currentSettings();
    if (settings) save("/presets", "POST", { name, settings }, `Saved "${name.trim()}".`);
  };

  const replace = () => {
    const settings = currentSettings();
    const existing = presets.find((p) => p.id === replaceId);
    if (settings && existing) save(`/presets/${existing.id}`, "PUT", { settings }, `Replaced "${existing.name}".`);
  };

  const update = () => {
    const settings = currentSettings();
    if (settings) save(`/presets/${loaded.id}`, "PUT", { settings }, `Updated "${loaded.name}".`);
  };

  const remove = async () => {
    setBusy(true);
    const response = await request(`/presets/${loaded.id}`, { method: "DELETE" });
    setBusy(false);
    setConfirmDelete(false);

    if (response.ok) {
      setPresets((current) => current.filter((p) => p.id !== loaded.id));
      setMessage({ text: `Deleted "${loaded.name}".` });
      setLoadedId(null);
    } else {
      setMessage({ text: response.message, error: true });
    }
  };

  return (
    <div className="form-group preset-bar">
      <label className="input-label" htmlFor="preset-select">Presets</label>
      <div className="preset-row">
        <select
          id="preset-select"
          className="input"
          value={loadedId ?? ""}
          onChange={(event) => load(event.target.value)}
          disabled={!presets?.length}
        >
          <option value="">{presets === null ? "Loading…" : presets.length ? "Load a Saved Preset…" : "No Saved Presets Yet"}</option>
          {(presets || []).map((preset) => (
            <option key={preset.id} value={preset.id}>{preset.name}</option>
          ))}
        </select>

        {loaded && changed && (
          <Button variant="outline" size="sm" onClick={update} disabled={busy}>Update Preset</Button>
        )}
        <Button
          variant="outline"
          size="sm"
          onClick={() => {
            setNaming(true);
            setName("");
            setMessage(null);
          }}
          disabled={busy || naming}
        >
          Save as New
        </Button>
        {loaded && (confirmDelete ? (
          <>
            <Button variant="outline" size="sm" onClick={() => setConfirmDelete(false)} disabled={busy}>Keep</Button>
            <Button variant="danger-solid" size="sm" onClick={remove} disabled={busy}>Delete "{loaded.name}"</Button>
          </>
        ) : (
          <Button variant="danger" size="sm" onClick={() => setConfirmDelete(true)} disabled={busy}>Delete</Button>
        ))}
      </div>

      {naming && (
        <div className="preset-row mt-xs">
          <input
            className="input"
            value={name}
            placeholder="Preset Name, e.g. CS101 Tutorial"
            onChange={(event) => {
              setName(event.target.value);
              setReplaceId(null);
              setMessage(null);
            }}
            onKeyDown={(event) => {
              if (event.key === "Enter") {
                event.preventDefault();
                if (name.trim()) saveNew();
              }
            }}
            maxLength={MAX_NAME_LENGTH}
            aria-label="Preset Name"
            autoFocus
          />
          <Button variant="primary" size="sm" onClick={saveNew} disabled={busy || !name.trim()}>Save</Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => {
              setNaming(false);
              setReplaceId(null);
              setMessage(null);
            }}
            disabled={busy}
          >
            Cancel
          </Button>
        </div>
      )}

      {message && (
        <div className={message.error ? "input-error" : "input-hint"} role={message.error ? "alert" : "status"}>
          {message.text}
          {replaceId && (
            <button type="button" className="btn-text preset-replace" onClick={replace} disabled={busy}>Replace It</button>
          )}
        </div>
      )}
      {!message && loaded && (
        <div className="input-hint">
          {changed ? `Changed from "${loaded.name}". Update it, or Save as a New Preset.` : `Using "${loaded.name}".`}
        </div>
      )}
    </div>
  );
}
