import { Navigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';

// ProtectedStudentRoute - Requires student to have enter details or join tutorial
export function ProtectedStudentRoute({ children, requiresJoin = false }) {
  const { studentDetails, isValidating } = useAuth();

  if (isValidating) {
    return <div>Loading...</div>;
  }

  // Student must have details to access student pages
  if (!studentDetails) {
    return <Navigate to="/" replace />;
  }

  //  Student must have joined a tutorial
  if (requiresJoin && !studentDetails.code) {
    return <Navigate to="/join" replace />;
  }

  return children;
}

// ProtectedStaffRoute - Requires staff authentication
export function ProtectedStaffRoute({ children }) {
  const { staffStatus, isValidating } = useAuth();

  if (isValidating) {
    return <div>Loading...</div>;
  }

  if (!staffStatus) {
    return <Navigate to="/staff/login" replace />;
  }

  return children;
}

// PublicRoute - Accessible to all users
export function PublicRoute({ children }) {
  const { isValidating } = useAuth();

  if (isValidating) {
    return <div>Loading...</div>;
  }

  return children;
}
