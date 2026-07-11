export function PageHeader({ title, description }: { title: string; description: string }) {
  return (
    <div className="mb-5 flex flex-col gap-1">
      <h1 className="text-2xl font-semibold tracking-normal text-slate-50">{title}</h1>
      <p className="max-w-3xl text-sm text-slate-400">{description}</p>
    </div>
  );
}
