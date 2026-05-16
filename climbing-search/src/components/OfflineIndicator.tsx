import React, { useEffect, useState } from 'react';
import { setupOfflineDetection } from '../utils/registerSW';

/**
 * Component that shows an indicator when the app is offline
 */
const OfflineIndicator: React.FC = () => {
  const [isOffline, setIsOffline] = useState(!navigator.onLine);

  useEffect(() => {
    // Setup offline detection and return cleanup to remove listeners on unmount
    return setupOfflineDetection((isOnline) => {
      setIsOffline(!isOnline);
    });
  }, []);

  if (!isOffline) {
    return null;
  }

  return (
    <div
      className="fixed bottom-4 right-4 bg-red-500 text-white px-4 py-2 rounded-md shadow-lg z-50 flex items-center"
      role="alert"
    >
      <svg
        xmlns="http://www.w3.org/2000/svg"
        className="h-5 w-5 mr-2"
        viewBox="0 0 20 20"
        fill="currentColor"
      >
        <path
          fillRule="evenodd"
          d="M13.477 14.89A6 6 0 015.11 6.524l8.367 8.368zm1.414-1.414L6.524 5.11a6 6 0 018.367 8.367zM18 10a8 8 0 11-16 0 8 8 0 0116 0z"
          clipRule="evenodd"
        />
      </svg>
      <span>You're offline. Using cached data.</span>
    </div>
  );
};

export default OfflineIndicator;
