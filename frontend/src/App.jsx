import { Routes, Route } from "react-router-dom";

// Student pages
import JoinSession from "./pages/student/JoinSession";
import EnterAttributes from "./pages/student/EnterAttributes";
import WaitingLobby from "./pages/student/WaitingLobby";
import GroupView from "./pages/student/GroupView";

// Staff pages
import SessionSetup from './pages/staff/SessionSetup';
import SessionLobby from './pages/staff/SessionLobby';
import GroupFormation from './pages/staff/GroupFormation';
import DiscussionBoard from './pages/staff/DiscussionBoard';

function App() {
  return (
    <Routes>
      {/* Basic Route */}
      <Route path="/" element={<JoinSession />} />

      {/* Student */}
      <Route path="/student/join" element={<JoinSession />} />
      <Route path="/student/attributes" element={<EnterAttributes />} />
      <Route path="/student/waiting" element={<WaitingLobby />} />
      <Route path="/student/group" element={<GroupView />} />

      {/* Staff */}
      <Route path="/staff/setup" element={<SessionSetup />} />
      <Route path="/staff/lobby" element={<SessionLobby />} />
      <Route path="/staff/groups" element={<GroupFormation />} />
      <Route path="/staff/discussion" element={<DiscussionBoard />} />
    </Routes>
  );
}

export default App;
