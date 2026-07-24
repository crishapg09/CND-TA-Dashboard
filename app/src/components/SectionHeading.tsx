export function SectionHeading({ n, title, bg = '#0B5A8A' }: { n: number; title: string; bg?: string }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 12, margin: '34px 0 14px' }}>
      <div
        style={{
          width: 26,
          height: 26,
          borderRadius: 7,
          background: bg,
          color: '#fff',
          fontSize: 13,
          fontWeight: 700,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
        }}
      >
        {n}
      </div>
      <div style={{ fontSize: 18, fontWeight: 700 }}>{title}</div>
    </div>
  );
}
