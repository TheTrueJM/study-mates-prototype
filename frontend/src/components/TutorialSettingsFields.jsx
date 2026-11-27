import NumberInput from "./NumberInput";
import SliderInput from "./SliderInput";
import Switch from "./Switch";
import AttributeToggleList from "./AttributeToggleList";
import CustomAttributeList from "./CustomAttributeList";
import PresetBar from "./PresetBar";
import { MIN_GROUP_SIZE, MAX_GROUP_SIZE, MIN_DISCUSSION_MINUTES, MAX_DISCUSSION_MINUTES } from "../constants/settings";


// Group Size, Group Limit, Discussion Time, and Student Detail Settings for a Tutorial
export default function TutorialSettingsFields({ values, onChange, errors = {} }) {
  const set = (key) => (value) => onChange({ ...values, [key]: value });

  return (
    <>
      <PresetBar values={values} onChange={onChange} />

      <SliderInput
        name="group-size"
        label="Students per Group"
        value={values.groupSize}
        min={MIN_GROUP_SIZE}
        max={MAX_GROUP_SIZE}
        onChange={set("groupSize")}
        hint={errors.groupSize || "Students left over form a Smaller Group, or join another Group if there's only one Student."}
      />

      <div className="form-group">
        <div className="input-label-row">
          <label className="input-label" htmlFor="limit-groups">Limit Number of Groups</label>
          <Switch
            id="limit-groups"
            label="Limit Number of Groups"
            onLabel="On"
            offLabel="Off"
            checked={values.limitGroups}
            onChange={set("limitGroups")}
          />
        </div>
        {values.limitGroups ? (
          <NumberInput
            name="max-groups"
            value={values.maxGroups}
            min={2}
            placeholder="e.g. 8"
            onChange={set("maxGroups")}
            error={errors.maxGroups}
            hint="For Example, the number of Tables in the Room. Groups grow larger if needed."
          />
        ) : (
          <p className="input-hint">As many Groups as needed will be Formed.</p>
        )}
      </div>

      <NumberInput
        name="discussion-time"
        label="Discussion Time per Round (minutes)"
        value={values.discussionTime}
        min={MIN_DISCUSSION_MINUTES}
        max={MAX_DISCUSSION_MINUTES}
        placeholder="5"
        onChange={set("discussionTime")}
        error={errors.discussionTime}
      />

      <div className="form-group">
        <div className="input-label-row">
          <label className="input-label" htmlFor="shortlisting">Teammate Shortlist</label>
          <Switch
            id="shortlisting"
            label="Teammate Shortlist"
            onLabel="On"
            offLabel="Off"
            checked={!!values.shortlisting}
            onChange={set("shortlisting")}
          />
        </div>
        <p className="input-hint">
          Students can Shortlist Classmates they'd like to Team Up with. Students who Shortlist each other are notified at the Wrap-Up.
        </p>
      </div>

      <AttributeToggleList
        value={values.availableAttributes}
        onChange={set("availableAttributes")}
        hasCustom={(values.customAttributes || []).length > 0}
      />

      <CustomAttributeList value={values.customAttributes || []} onChange={set("customAttributes")} />
    </>
  );
}
