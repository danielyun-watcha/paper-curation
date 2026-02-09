export default function StudyLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="max-w-[1444px] mx-auto">
      {children}
    </div>
  );
}
