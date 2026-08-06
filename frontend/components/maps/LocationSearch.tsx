"use client";

import { useEffect, useState } from "react";
import { useAuth } from "@/components/AuthProvider";
import { api } from "@/lib/api";
import type { GeocodingResult } from "@/lib/types";

export function LocationSearch({ id, label, value, onChange, onSelect, placeholder = "Buscar ciudad, barrio o lugar en Paraguay" }: { id: string; label: string; value: string; onChange: (value: string) => void; onSelect: (result: GeocodingResult) => void; placeholder?: string }) {
  const { token } = useAuth();
  const [results, setResults] = useState<GeocodingResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [searched, setSearched] = useState(false);
  const [error, setError] = useState(false);
  useEffect(() => {
    if (!token || value.trim().length < 3) return;
    const controller = new AbortController();
    const timer = window.setTimeout(() => { setLoading(true);setError(false); api.geocode(value, token, controller.signal).then((items)=>{setResults(items);setSearched(true);}).catch((caught) => {if(caught?.name!=="AbortError"){setResults([]);setSearched(true);setError(true);}}).finally(() => setLoading(false)); }, 450);
    return () => { window.clearTimeout(timer); controller.abort(); };
  }, [token, value]);
  const visibleResults = value.trim().length >= 3 ? results : [];
  return <div className="location-search form-field"><label htmlFor={id}>{label}</label><input id={id} value={value} onChange={(event) => {onChange(event.target.value);setSearched(false);setError(false);}} autoComplete="off" placeholder={placeholder} required />{loading && <span className="map-help">Buscando lugares…</span>}{error&&!loading&&<span className="map-help" role="alert">No pudimos buscar lugares. Intentá nuevamente.</span>}{searched&&!loading&&!error&&visibleResults.length===0&&<span className="map-help">No encontramos lugares en Paraguay con ese nombre.</span>}{visibleResults.length > 0 && <ul className="location-results" role="listbox">{visibleResults.map((item) => <li key={`${item.latitude}-${item.longitude}`}><button type="button" onClick={() => { onSelect(item); setResults([]);setSearched(false); }}>{item.label}</button></li>)}</ul>}</div>;
}
