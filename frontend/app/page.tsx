import Link from "next/link";

export default function Home() {
  return (
    <>
      <section className="container grid min-h-[72vh] items-center gap-10 py-16 lg:grid-cols-2">
        <div>
          <p className="mb-4 font-bold uppercase tracking-[0.18em] text-emerald-700">
            Compartimos el camino
          </p>
          <h1 className="max-w-3xl text-5xl font-black leading-tight text-slate-950 md:text-6xl">
            Viajar juntos hace más cercana nuestra comunidad.
          </h1>
          <p className="mt-6 max-w-2xl text-lg leading-8 text-slate-600">
            Publicá tu próximo trayecto o encontrá personas que viajan hacia el
            mismo destino. Simple, seguro y pensado para Paraguay.
          </p>
          <div className="mt-8 flex flex-wrap gap-3">
            <Link className="button-primary" href="/registro">
              Comenzar ahora
            </Link>
            <Link className="button-secondary" href="/login">
              Ya tengo cuenta
            </Link>
          </div>
        </div>
        <div className="form-card relative overflow-hidden">
          <div className="absolute -right-20 -top-20 h-56 w-56 rounded-full bg-amber-300/30" />
          <p className="eyebrow">Tu próximo trayecto</p>
          <div className="relative mt-8 space-y-6">
            {[
              ["1", "Creá tu cuenta"],
              ["2", "Elegí o publicá un viaje"],
              ["3", "Compartí el camino"],
            ].map(([number, label]) => (
              <div className="flex items-center gap-4" key={number}>
                <span className="grid h-11 w-11 place-items-center rounded-full bg-emerald-700 font-black text-white">
                  {number}
                </span>
                <span className="text-lg font-bold text-slate-800">{label}</span>
              </div>
            ))}
          </div>
        </div>
      </section>
      <section className="bg-emerald-950 py-10 text-white">
        <div className="container grid gap-6 text-center md:grid-cols-3">
          <div><strong className="text-2xl">Comunidad</strong><p className="mt-2 text-emerald-100">Conexiones para trayectos cotidianos.</p></div>
          <div><strong className="text-2xl">Control</strong><p className="mt-2 text-emerald-100">Vos decidís qué viaje crear o compartir.</p></div>
          <div><strong className="text-2xl">Claridad</strong><p className="mt-2 text-emerald-100">Estados y reglas visibles en cada paso.</p></div>
        </div>
      </section>
    </>
  );
}
