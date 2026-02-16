import { Routes, Route } from "react-router-dom";
import Navbar from "./components/Navbar";

// Student pages
import JoinSession from "./pages/student/JoinSession";
import EnterAttributes from "./pages/student/EnterAttributes";
import WaitingLobby from "./pages/student/WaitingLobby";
import GroupView from "./pages/student/GroupView";

// Staff pages
import Login from './pages/staff/Login';
import SessionSetup from './pages/staff/SessionSetup';
import SessionLobby from './pages/staff/SessionLobby';
import GroupFormation from './pages/staff/GroupFormation';
import DiscussionBoard from './pages/staff/DiscussionBoard';

function App() {
  return (
    <>
      <Navbar />
      <Routes>
        {/* Home */}
        <Route path="/" element={<JoinSession />} />

        {/* Student */}
        {/* Use Route '/join/:code' to prefill code and go to attributes (For QR Code) */}
        <Route path="/join" element={<JoinSession />} /> 
        <Route path="/attributes" element={<EnterAttributes />} />
        <Route path="/waiting" element={<WaitingLobby />} />
        <Route path="/group" element={<GroupView />} />

        {/* Staff */}
        <Route path="/staff/login" element={<Login />} />
        <Route path="/staff/" element={<SessionSetup />} />
        <Route path="/staff/tutorial/:code" element={<SessionLobby />} />
        <Route path="/staff/groups" element={<GroupFormation />} />
        <Route path="/staff/discussion" element={<DiscussionBoard />} />
      </Routes>
    </>
  );
}

export default App;
