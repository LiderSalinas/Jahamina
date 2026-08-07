"use client";

import { useEffect, useId, useState } from "react";
import { useAuth } from "@/components/AuthProvider";
import { api } from "@/lib/api";
import type { GeocodingResult } from "@/lib/types";

interface LocationSearchProps {
  id: string;
  label: string;
  value: string;
  onChange: (value: string) => void;
  onSelect: (result: GeocodingResult) => void;
  placeholder?: string;
}

export function LocationSearch({ id, label, value, onChange, onSelect, placeholder = "Buscar ciudad, barrio o lugar en Paraguay" }: LocationSearchProps) {
  const { token } = useAuth();
  const statusId = useId();
  const [results, setResults] = useState<GeocodingResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [searched, setSearched] = useState(false);
  const [error, setError] = useState(false);

  useEffect(() => {
    const query = value.trim();
    if (!token || query.length < 3) return;
    const controller = new AbortController();
    const timer = window.setTimeout(() => {
      setLoading(true);
      setError(false);
      api.geocode(query, token, controller.signal)
        .then((items) => {
          setResults(items.slice(0, 6));
          setSearched(true);
        })
        .catch((caught: unknown) => {
          if (caught instanceof DOMException && caught.name === "AbortError") return;
          setResults([]);
          setSearched(true);
          setError(true);
        })
        .finally(() => {
          if (!controller.signal.aborted) setLoading(false);
        });
    }, 300);
    return () => {
      window.clearTimeout(timer);
      controller.abort();
    };
  }, [token, value]);

  const visibleResults = value.trim().length >= 3 ? results : [];
  return (
    <div className="location-search form-field">
      <label htmlFor={id}>{label}</label>
      <input
        id={id}
        value={value}
        onChange={(event) => {
          onChange(event.target.value);
          setResults([]);
          setLoading(false);
          setSearched(false);
          setError(false);
        }}
        aria-autocomplete="list"
        aria-controls={`${id}-results`}
        aria-describedby={statusId}
        autoComplete="off"
        placeholder={placeholder}
        required
      />
      <span id={statusId} className="map-help" aria-live="polite">
        {loading ? "Buscando…" : error ? "No pudimos buscar lugares. Intentá nuevamente." : searched && visibleResults.length === 0 ? "No encontramos lugares en Paraguay con ese nombre." : ""}
      </span>
      {visibleResults.length > 0 && (
        <ul id={`${id}-results`} className="location-results" role="listbox" aria-label={`Sugerencias para ${label}`}>
          {visibleResults.map((item) => (
            <li key={`${item.latitude}-${item.longitude}`} role="option" aria-selected="false">
              <button type="button" onClick={() => { onSelect(item); setResults([]); setSearched(false); }}>
                <strong>{item.primary ?? item.label.split(",")[0]}</strong>
                <span>{item.secondary ?? item.label.split(",").slice(1).join(",").trim()}</span>
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
