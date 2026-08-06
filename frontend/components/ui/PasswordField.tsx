"use client";

import { InputHTMLAttributes, useState } from "react";

export function PasswordField({ id, label = "Contraseña", ...props }: InputHTMLAttributes<HTMLInputElement> & { id: string; label?: string }) {
  const [visible, setVisible] = useState(false);
  return <div className="form-field"><label htmlFor={id}>{label}</label><div className="password-control"><input {...props} id={id} type={visible ? "text" : "password"}/><button type="button" aria-label={visible ? "Ocultar contraseña" : "Mostrar contraseña"} aria-pressed={visible} onClick={() => setVisible(value => !value)}>{visible ? "Ocultar" : "Mostrar"}</button></div></div>;
}
