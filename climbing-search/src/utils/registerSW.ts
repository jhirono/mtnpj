/**
 * Service worker registration and offline detection utilities
 */

/**
 * Register the service worker for offline functionality
 */
export function registerServiceWorker() {
  if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
      navigator.serviceWorker.register('/sw.js')
        .then(registration => {
          console.log('Service Worker registered successfully:', registration.scope);
        })
        .catch(error => {
          console.error('Service Worker registration failed:', error);
        });
    });
  }
}

/**
 * Setup offline detection and callback when online status changes
 * @param callback Function to call when online status changes
 * @returns Cleanup function that removes the event listeners
 */
export function setupOfflineDetection(callback: (isOnline: boolean) => void): () => void {
  // Initial status
  callback(navigator.onLine);

  // Store handler references so they can be removed later
  const onOnline = () => callback(true);
  const onOffline = () => callback(false);

  window.addEventListener('online', onOnline);
  window.addEventListener('offline', onOffline);

  return () => {
    window.removeEventListener('online', onOnline);
    window.removeEventListener('offline', onOffline);
  };
}

/**
 * Check if the app is currently online
 * @returns Boolean indicating online status
 */
export function isOnline(): boolean {
  return navigator.onLine;
}
