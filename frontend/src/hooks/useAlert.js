import { useState, useRef, useEffect } from 'react';

/**
 * Custom hook for managing alerts with auto-dismiss functionality
 * @returns {Object} Alert state and methods
 */
export function useAlert() {
  const [alert, setAlert] = useState(null);
  const alertTimeoutRef = useRef(null);

  useEffect(() => {
    // Cleanup timeout on unmount
    return () => {
      if (alertTimeoutRef.current) {
        clearTimeout(alertTimeoutRef.current);
      }
    };
  }, []);

  const showAlert = (variant, message) => {
    // Clear any existing timeout
    if (alertTimeoutRef.current) {
      clearTimeout(alertTimeoutRef.current);
    }

    setAlert({ variant, message });

    // Success alerts stay longer (7 seconds), errors stay for 5 seconds
    const timeout = variant === 'success' ? 7000 : 5000;
    alertTimeoutRef.current = setTimeout(() => {
      setAlert(null);
      alertTimeoutRef.current = null;
    }, timeout);
  };

  const clearAlert = () => {
    if (alertTimeoutRef.current) {
      clearTimeout(alertTimeoutRef.current);
      alertTimeoutRef.current = null;
    }
    setAlert(null);
  };

  return { alert, showAlert, clearAlert };
}

