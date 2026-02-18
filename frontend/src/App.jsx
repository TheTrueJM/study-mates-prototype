import { Routes, Route } from "react-router-dom";
import Navbar from "./components/Navbar";

// Student pages
import JoinTutorial from "./pages/student/JoinTutorial";
import EnterDetails from "./pages/student/EnterDetails";
import StudentTutorial from './pages/student/Tutorial';

// Staff pages
import Login from './pages/staff/Login';
import TutorialSetup from './pages/staff/TutorialSetup';
import StaffTutorial from './pages/staff/Tutorial';

function App() {
  return (
    <>
      <Navbar />
      <Routes>
        {/* Home */}
        <Route path="/" element={<EnterDetails />} />

        {/* Student */}
        {/* Use Route '/tutorial/:code' for tutorial */}
        <Route path="/details" element={<EnterDetails />} />
        <Route path="/join" element={<JoinTutorial />} /> 
        <Route path="/tutorial" element={<StudentTutorial />} />

        {/* Staff */}
        <Route path="/staff/login" element={<Login />} />
        <Route path="/staff/" element={<TutorialSetup />} />
        <Route path="/staff/tutorial/:code" element={<StaffTutorial />} />
      </Routes>
    </>
  );
}

export default App;
