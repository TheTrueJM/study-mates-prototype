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
    },
  };
}
