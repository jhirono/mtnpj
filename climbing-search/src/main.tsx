import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.tsx'
import { registerSW } from 'virtual:pwa-register'

// VitePWA manages SW registration. Show a reload prompt when a new version is ready.
registerSW({
  onNeedRefresh() {
    const banner = document.createElement('div');
    banner.id = 'sw-update-banner';
    banner.style.cssText = 'position:fixed;bottom:0;left:0;right:0;background:#1d4ed8;color:#fff;text-align:center;padding:10px 16px;z-index:9999;font-size:14px;display:flex;align-items:center;justify-content:center;gap:12px;';
    banner.innerHTML = 'New version available. <button onclick="location.reload()" style="background:#fff;color:#1d4ed8;border:none;padding:4px 12px;border-radius:4px;cursor:pointer;font-weight:600;">Reload</button>';
    document.body.appendChild(banner);
  },
});

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
