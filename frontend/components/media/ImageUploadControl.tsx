"use client";

import { useEffect, useId, useRef, useState } from "react";

const ALLOWED_TYPES = new Set(["image/jpeg", "image/png", "image/webp"]);
const MAX_BYTES = 5 * 1024 * 1024;

export function ImageUploadControl({ hasImage, uploading, onUpload, onDelete, description }: {
  hasImage: boolean;
  uploading: boolean;
  onUpload: (file: File) => Promise<void>;
  onDelete: () => Promise<void>;
  description: string;
}) {
  const inputId = useId();
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState("");
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const previewRef = useRef("");

  useEffect(() => () => { if (previewRef.current) URL.revokeObjectURL(previewRef.current); }, []);

  const clearSelection = () => {
    if (previewRef.current) URL.revokeObjectURL(previewRef.current);
    previewRef.current = ""; setPreview(""); setFile(null);
  };

  const select = (next: File | undefined) => {
    setError(""); setNotice("");
    if (!next) { clearSelection(); return; }
    if (!ALLOWED_TYPES.has(next.type)) { setError("Elegí una imagen JPEG, PNG o WebP."); return; }
    if (next.size > MAX_BYTES) { setError("La imagen no puede superar 5 MB."); return; }
    if (previewRef.current) URL.revokeObjectURL(previewRef.current);
    previewRef.current = URL.createObjectURL(next); setPreview(previewRef.current); setFile(next);
  };
  const upload = async () => {
    if (!file || uploading) return;
    try { await onUpload(file); clearSelection(); setNotice("Foto actualizada."); }
    catch (caught) { setError(caught instanceof Error ? caught.message : "No pudimos subir la imagen."); }
  };
  const remove = async () => {
    if (uploading) return;
    try { await onDelete(); clearSelection(); setNotice("Foto eliminada."); }
    catch (caught) { setError(caught instanceof Error ? caught.message : "No pudimos eliminar la imagen."); }
  };

  return <div className="image-upload-control">
    <div><b>Foto</b><p>{description}</p></div>
    {preview && <div className="image-local-preview">
      {/* Local object URLs are intentionally rendered without a remote host allowlist. */}
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img src={preview} alt="Vista previa de la imagen seleccionada"/>
    </div>}
    <input id={inputId} type="file" accept="image/jpeg,image/png,image/webp" disabled={uploading} onChange={(event) => select(event.target.files?.[0])}/>
    <div className="image-upload-actions"><label className="button-secondary" htmlFor={inputId}>{file ? "Elegir otra" : hasImage ? "Cambiar foto" : "Agregar foto"}</label>{file && <button className="button-primary" type="button" disabled={uploading} onClick={() => void upload()}>{uploading ? "Subiendo…" : "Guardar foto"}</button>}{hasImage && !file && <button className="text-danger" type="button" disabled={uploading} onClick={() => void remove()}>{uploading ? "Eliminando…" : "Eliminar foto"}</button>}</div>
    {error && <p className="field-error" role="alert">{error}</p>}
    {notice && <p className="success-message" role="status">{notice}</p>}
  </div>;
}
