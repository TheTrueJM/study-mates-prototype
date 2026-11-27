import { useEffect, useState } from "react";

import { useAuth } from "../contexts/AuthContext";
import { CUSTOM_LIMITS, customAttributeMeta, generateCustomId } from "../constants/attributes";

import Button from "./Button";
import CustomAttributeEditor from "./CustomAttributeEditor";


const definitionOf = ({ label, hint, options, multiple, matching }) => ({ label, hint, options, multiple, matching });


/**
 * The Custom Details of a Tutorial, which Staff create (or Add from those Saved to their Account).
 * Each works like the Built-In Details: Students pick from its Options, and it can be used for Matching.
 */
export default function CustomAttributeList({ value = [], onChange }) {
  const { isAccount, request } = useAuth();

  const [editing, setEditing] = useState(null); // "new" | Custom Detail ID
  const [saved, setSaved] = useState(null); // Saved Details (null until loaded)
  const [savedError, setSavedError] = useState("");
  const [deleting, setDeleting] = useState(null); // Saved Detail ID awaiting confirmation

  useEffect(() => {
    if (!isAccount) return undefined;
    let cancelled = false;
    request("/attributes").then((response) => {
      if (cancelled) return;
      if (response.ok) setSaved(response.data.attributes || []);
      else setSavedError(response.message);
    });
    return () => {
      cancelled = true;
    };
  }, [isAccount, request]);

  const atLimit = value.length >= CUSTOM_LIMITS.details;
  const editingDetail = value.find((detail) => detail.id === editing);
  const otherLabels = value.filter((detail) => detail.id !== editing).map((detail) => detail.label);

  // Returns an Error Message if Saving to the Account Failed
  const submit = async (values, saveToAccount) => {
    let savedId = editingDetail?.saved_id ?? null;

    if (saveToAccount) {
      const response = savedId
        ? await request(`/attributes/${savedId}`, { method: "PUT", body: definitionOf(values) })
        : await request("/attributes", { method: "POST", body: definitionOf(values) });
      if (!response.ok) return response.message;

      const savedDetail = response.data.attribute;
      savedId = savedDetail.id;
      setSaved((current) => [...(current || []).filter((s) => s.id !== savedId), savedDetail]
        .sort((a, b) => a.label.localeCompare(b.label)));
    }

    const detail = { ...definitionOf(values), id: editingDetail?.id ?? generateCustomId(), saved_id: savedId };
    onChange(editingDetail ? value.map((d) => (d.id === detail.id ? detail : d)) : [...value, detail]);
    setEditing(null);
    return null;
  };

  const addSaved = (savedDetail) => {
    onChange([...value, { ...definitionOf(savedDetail), id: generateCustomId(), saved_id: savedDetail.id }]);
  };

  const deleteSaved = async (savedId) => {
    const response = await request(`/attributes/${savedId}`, { method: "DELETE" });
    setDeleting(null);
    if (!response.ok) {
      setSavedError(response.message);
      return;
    }
    setSaved((current) => current.filter((s) => s.id !== savedId));
    // Details already in this Session are kept, but are no longer linked to the Saved Copy
    onChange(value.map((d) => (d.saved_id === savedId ? { ...d, saved_id: null } : d)));
  };

  const unusedSaved = (saved || []).filter((s) => !value.some((d) => d.saved_id === s.id));

  return (
    <div className="form-group">
      <span className="input-label" id="custom-details-label">Custom Details</span>
      <p className="input-hint mb-xs">
        Ask Students your own Questions, with Options for them to choose from.
      </p>

      {value.length > 0 && (
        <ul className="custom-list" aria-labelledby="custom-details-label">
          {value.map((detail) => (
            <li key={detail.id} className="custom-item">
              {editing === detail.id ? (
                <CustomAttributeEditor
                  initial={detail}
                  otherLabels={otherLabels}
                  canSave={isAccount}
                  onSubmit={submit}
                  onCancel={() => setEditing(null)}
                />
              ) : (
                <div className="custom-item-row">
                  <span className="attr-toggle-text">
                    <span className="attr-toggle-label">{detail.label}</span>
                    <span className="attr-toggle-hint">{customAttributeMeta(detail).staffHint}</span>
                  </span>
                  <span className={`tag ${detail.matching !== "display" ? "tag-primary" : ""}`}>
                    {detail.matching !== "display" ? "Matching" : "Display only"}
                  </span>
                  <Button variant="outline" size="sm" onClick={() => setEditing(detail.id)} disabled={!!editing}>Edit</Button>
                  <Button
                    variant="danger"
                    size="sm"
                    onClick={() => onChange(value.filter((d) => d.id !== detail.id))}
                    disabled={!!editing}
                    aria-label={`Remove ${detail.label}`}
                  >
                    Remove
                  </Button>
                </div>
              )}
            </li>
          ))}
        </ul>
      )}

      {editing === "new" ? (
        <div className="custom-item">
          <CustomAttributeEditor
            otherLabels={otherLabels}
            canSave={isAccount}
            onSubmit={submit}
            onCancel={() => setEditing(null)}
          />
        </div>
      ) : (
        <Button variant="outline" size="sm" onClick={() => setEditing("new")} disabled={atLimit || !!editing}>
          + Add Custom Detail
        </Button>
      )}
      {atLimit && <p className="input-hint mt-xs">A Session can have up to {CUSTOM_LIMITS.details} Custom Details.</p>}

      {isAccount ? (
        saved && saved.length > 0 && (
          <details className="disclosure mt-sm">
            <summary>Your Saved Details ({saved.length})</summary>
            <div className="disclosure-body">
              {unusedSaved.length === 0 && <p className="text-muted">All of your Saved Details are in this Session.</p>}
              <ul className="custom-list">
                {unusedSaved.map((savedDetail) => (
                  <li key={savedDetail.id} className="custom-item custom-item-row">
                    <span className="attr-toggle-text">
                      <span className="attr-toggle-label">{savedDetail.label}</span>
                      <span className="attr-toggle-hint">{customAttributeMeta(savedDetail).staffHint}</span>
                    </span>
                    {deleting === savedDetail.id ? (
                      <>
                        <Button variant="outline" size="sm" onClick={() => setDeleting(null)}>Keep</Button>
                        <Button variant="danger-solid" size="sm" onClick={() => deleteSaved(savedDetail.id)}>Delete</Button>
                      </>
                    ) : (
                      <>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => addSaved(savedDetail)}
                          disabled={atLimit || value.some((d) => d.label.toLowerCase() === savedDetail.label.toLowerCase())}
                        >
                          Add
                        </Button>
                        <Button
                          variant="danger"
                          size="sm"
                          onClick={() => setDeleting(savedDetail.id)}
                          aria-label={`Delete Saved ${savedDetail.label}`}
                        >
                          Delete
                        </Button>
                      </>
                    )}
                  </li>
                ))}
              </ul>
              {savedError && <p className="input-error" role="alert">{savedError}</p>}
            </div>
          </details>
        )
      ) : (
        <p className="input-hint mt-xs">Sign in with a Staff Account to Save Custom Details for your Future Sessions.</p>
      )}
    </div>
  );
}
