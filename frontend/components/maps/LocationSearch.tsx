"use client";

import { useEffect, useState } from "react";
import { useAuth } from "@/components/AuthProvider";
import { api } from "@/lib/api";
import type { GeocodingResult } from "@/lib/types";

export function LocationSearch({ id, label, value, onChange, onSelect }: { id: string; label: string; value: string; onChange: (value: string) => void; onSelect: (result: GeocodingResult) => void }) {
  const { token } = useAuth();
  const [results, setResults] = useState<GeocodingResult[]>([]);
  const [loading, setLoading] = useState(false);
  useEffect(() => {
    if (!token || value.trim().length < 3) return;
    const controller = new AbortController();
    const timer = window.setTimeout(() => { setLoading(true); api.geocode(value, token, controller.signal).then(setResults).catch(() => setResults([])).finally(() => setLoading(false)); }, 450);
    return () => { window.clearTimeout(timer); controller.abort(); };
  }, [token, value]);
  const visibleResults = value.trim().length >= 3 ? results : [];
  return <div className="location-search form-field"><label htmlFor={id}>{label}</label><input id={id} value={value} onChange={(event) => onChange(event.target.value)} autoComplete="off" required />{loading && <span className="map-help">Buscando…</span>}{visibleResults.length > 0 && <ul className="location-results" role="listbox">{visibleResults.map((item) => <li key={`${item.latitude}-${item.longitude}`}><button type="button" onClick={() => { onSelect(item); setResults([]); }}>{item.label}</button></li>)}</ul>}</div>;
}
