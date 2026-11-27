// Staff Account Limits and Validation (limits mirror backend/app/auth.py)

export const MIN_USERNAME_LENGTH = 3;
export const MAX_USERNAME_LENGTH = 50;
export const MIN_PASSWORD_LENGTH = 8;
export const MAX_PASSWORD_BYTES = 72;


/** Validates Sign Up Form Values, returning { account, errors } */
export function validateAccount(values) {
  const errors = {};

  const username = values.username.trim();
  if (username.length < MIN_USERNAME_LENGTH || username.length > MAX_USERNAME_LENGTH) {
    errors.username = `Enter between ${MIN_USERNAME_LENGTH} and ${MAX_USERNAME_LENGTH} Characters.`;
  }

  if (values.password.length < MIN_PASSWORD_LENGTH) {
    errors.password = `Enter at least ${MIN_PASSWORD_LENGTH} Characters.`;
  } else if (new TextEncoder().encode(values.password).length > MAX_PASSWORD_BYTES) {
    errors.password = "This Password is Too Long.";
  }

  if (!errors.password && values.confirmPassword !== values.password) {
    errors.confirmPassword = "The Passwords don't Match.";
  }

  return { errors, account: { username, password: values.password } };
}
