import React, { createContext, useState, useCallback, useEffect } from 'react';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [studentDetails, setStudentDetails] = useState(null);
  const [staffAuth, setStaffAuth] = useState(null);
  const [isValidating, setIsValidating] = useState(true);

  // Validate session on app load
  useEffect(() => {
    validateSession();
  }, []);

  const validateSession = useCallback(async () => {
    setIsValidating(true);
    const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || 'http://localhost:5000';

    try {
      const res = await fetch(`${BACKEND_URL}/session`, {
        credentials: 'include',
      });

      if (res.ok) {
        const data = await res.json();
        
        if (data.role === 'student' && data.details) {
          setStudentDetails(data.details);
          setStaffAuth(null);
        } else if (data.role === 'staff' && data.authenticated) {
          setStaffAuth({ username: data.username });
          setStudentDetails(null);
        }
      }
    } catch (error) {
      console.error('Session validation error:', error);
    } finally {
      setIsValidating(false);
    }
  }, []);

  const setStudent = useCallback((details) => {
    setStudentDetails(details);
    setStaffAuth(null);
  }, []);

  const setStaff = useCallback((username) => {
    setStaffAuth({ username });
    setStudentDetails(null);
  }, []);

  const logout = useCallback(async () => {
    const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || 'http://localhost:5000';
    
    try {
      await fetch(`${BACKEND_URL}/staff/logout`, {
        credentials: 'include',
      });
    } catch (error) {
      console.error('Logout error:', error);
    }

    setStudentDetails(null);
    setStaffAuth(null);
  }, []);

  return (
    <AuthContext.Provider
      value={{
        studentDetails,
        staffAuth,
        isValidating,
        setStudent,
        setStaff,
        logout,
        validateSession,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export default AuthContext;
