export default function Card({ title, subtitle, children }) {
  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900/70 p-4">
      {title && (
        <div className="mb-3">
          <h2 className="text-sm font-semibold text-slate-200">{title}</h2>
          {subtitle && <p className="text-xs text-slate-500">{subtitle}</p>}
        </div>
      )}
      {children}
    </div>
  );
}