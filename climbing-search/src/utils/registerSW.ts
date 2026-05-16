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
 */
export function setupOfflineDetection(callback: (isOnline: boolean) => void) {
  // Initial status
  callback(navigator.onLine);
  
  // Listen for changes
  window.addEventListener('online', () => callback(true));
  window.addEventListener('offline', () => callback(false));
}

/**
 * Check if the app is currently online
 * @returns Boolean indicating online status
 */
export function isOnline(): boolean {
  return navigator.onLine;
} 