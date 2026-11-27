// Tutorial Settings Limits and Validation (limits mirror backend/app/sockets/staff.py)

export const MIN_GROUP_SIZE = 2;
export const MAX_GROUP_SIZE = 10;
export const MIN_DISCUSSION_MINUTES = 1;
export const MAX_DISCUSSION_MINUTES = 60;


/** Validates Settings Form Values, returning { settings, errors } */
export function validateSettings(values) {
  const errors = {};

  const groupSize = Number(values.groupSize);
  if (!Number.isInteger(groupSize) || groupSize < MIN_GROUP_SIZE || groupSize > MAX_GROUP_SIZE) {
    errors.groupSize = `Choose between ${MIN_GROUP_SIZE} and ${MAX_GROUP_SIZE} Students per Group.`;
  }

  const maxGroups = Number(values.maxGroups);
  if (values.limitGroups && (!Number.isInteger(maxGroups) || maxGroups < 2)) {
    errors.maxGroups = "Enter a Whole Number of at least 2 Groups.";
  }

  const discussionTime = Number(values.discussionTime);
  if (values.discussionTime === "" || Number.isNaN(discussionTime)
    || discussionTime < MIN_DISCUSSION_MINUTES || discussionTime > MAX_DISCUSSION_MINUTES) {
    errors.discussionTime = `Enter between ${MIN_DISCUSSION_MINUTES} and ${MAX_DISCUSSION_MINUTES} Minutes.`;
  }

  return {
    errors,
    settings: {
      group_size: groupSize,
      max_groups: values.limitGroups ? maxGroups : null,
      discussion_time: discussionTime,
      available_attributes: values.availableAttributes,
      shortlisting: !!values.shortlisting,
      custom_attributes: (values.customAttributes || []).map(({ id, label, hint, options, multiple, matching, saved_id }) => (
        { id, label, hint, options, multiple, matching, saved_id: saved_id ?? null }
      )),
    },
  };
}


/** Converts Saved Settings (as a Tutorial is created with) into Settings Form Values */
export function settingsToValues(settings) {
  return {
    groupSize: settings.group_size,
    limitGroups: !!settings.max_groups,
    maxGroups: settings.max_groups ?? "",
    discussionTime: Math.round(settings.discussion_time * 100) / 100,
    availableAttributes: [...(settings.available_attributes || [])],
    customAttributes: (settings.custom_attributes || []).map((detail) => ({ ...detail, options: [...detail.options] })),
    shortlisting: !!settings.shortlisting,
  };
}

/** Whether Settings Form Values match some Saved Settings */
export function matchesSettings(values, settings) {
  const normalise = ({ group_size, max_groups, discussion_time, available_attributes = [], custom_attributes = [], shortlisting }) =>
    JSON.stringify([
      group_size, max_groups ?? null, Number(discussion_time), [...available_attributes].sort(), !!shortlisting,
      custom_attributes.map(({ label, hint, options, multiple, matching }) => [label, hint || "", options, multiple, matching]),
    ]);

  return normalise(validateSettings(values).settings) === normalise(settings);
}
