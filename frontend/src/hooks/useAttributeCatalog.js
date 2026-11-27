import { useMemo } from "react";

import { useTutorial } from "../contexts/TutorialContext";
import { buildAttributeCatalog } from "../constants/attributes";


/** The Details (Built-In and the Tutorial's Custom Details) Students can be asked for in the Current Tutorial */
export function useAttributeCatalog() {
  const { customAttributes } = useTutorial();
  return useMemo(() => buildAttributeCatalog(customAttributes), [customAttributes]);
}
