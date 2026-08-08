"use client";

import { useEffect, useState } from "react";

type BeforeInstallPromptEvent = Event & {
  prompt: () => Promise<void>;
  userChoice: Promise<{ outcome: "accepted" | "dismissed" }>;
};

function isStandalone() {
  return window.matchMedia("(display-mode: standalone)").matches
    || ("standalone" in navigator && Boolean((navigator as Navigator & { standalone?: boolean }).standalone));
}

function isIos() {
  return /iphone|ipad|ipod/i.test(navigator.userAgent)
    || (navigator.platform === "MacIntel" && navigator.maxTouchPoints > 1);
}

export function InstallPrompt() {
  const [deferredPrompt, setDeferredPrompt] = useState<BeforeInstallPromptEvent | null>(null);
  const [installed, setInstalled] = useState(false);
  const [iosInstall, setIosInstall] = useState(false);

  useEffect(() => {
    const standalone = isStandalone();
    // This synchronizes browser-only installation state after hydration.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setInstalled(standalone);
    if (standalone) return;
    if (isIos()) {
      setIosInstall(true);
      return;
    }

    const handleBeforeInstall = (event: Event) => {
      event.preventDefault();
      setDeferredPrompt(event as BeforeInstallPromptEvent);
    };
    const handleInstalled = () => {
      setInstalled(true);
      setDeferredPrompt(null);
    };
    window.addEventListener("beforeinstallprompt", handleBeforeInstall);
    window.addEventListener("appinstalled", handleInstalled);
    return () => {
      window.removeEventListener("beforeinstallprompt", handleBeforeInstall);
      window.removeEventListener("appinstalled", handleInstalled);
    };
  }, []);

  const install = async () => {
    if (!deferredPrompt) return;
    await deferredPrompt.prompt();
    await deferredPrompt.userChoice;
    setDeferredPrompt(null);
  };

  if (installed || (!deferredPrompt && !iosInstall)) return null;
  return <aside className="pwa-install-prompt" role="status" aria-live="polite">
    <div><b>{iosInstall ? "Instalá Jahamina" : "Instalar Jahamina"}</b><p>{iosInstall ? "Para instalar Jahamina en iPhone: Compartir → Añadir a pantalla de inicio" : "Accedé más rápido desde tu pantalla de inicio."}</p></div>
    {iosInstall ? <span className="pwa-install-hint" aria-hidden>↗</span> : <button className="button-primary" type="button" onClick={() => void install()}>Instalar</button>}
  </aside>;
}
