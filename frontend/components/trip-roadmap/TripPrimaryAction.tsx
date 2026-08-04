import type { ScenarioDefinition } from "./types";

export function TripPrimaryAction({ scenario, onAction, disabled = false }: { scenario: ScenarioDefinition; onAction?: () => void; disabled?: boolean }) {
  return <aside className="roadmap-primary-action" aria-label="Acción principal"><div><small>Tu siguiente paso</small><b>{scenario.primaryAction}</b></div><button type="button" disabled={disabled} onClick={onAction} aria-label={scenario.primaryAction}>{scenario.primaryAction}</button></aside>;
}
