interface HeaderProps {
  metaTotal: string;
  isQuality: boolean;
  coFrom: string;
  coUnassigned: string;
}

export function Header({ metaTotal, isQuality, coFrom, coUnassigned }: HeaderProps) {
  return (
    <div style={{ maxWidth: 1340, margin: '0 auto', padding: '0 24px' }}>
      <div
        style={{
          display: 'flex',
          alignItems: 'flex-end',
          justifyContent: 'space-between',
          gap: 24,
          flexWrap: 'wrap',
          padding: '30px 0 18px',
        }}
      >
        <div>
          <div style={{ fontSize: 11, letterSpacing: '.16em', textTransform: 'uppercase', color: '#1CABE2', fontWeight: 700 }}>
            Technical Assistance Request and Implementation
          </div>
          <div style={{ fontSize: 27, fontWeight: 700, letterSpacing: '-.01em', marginTop: 6 }}>
            TA Performance Management Dashboard
          </div>
        </div>
        <div style={{ textAlign: 'right', fontSize: 12, color: '#5B7186', lineHeight: 1.6 }}>
          {isQuality ? (
            <div>
              <span style={{ fontWeight: 700, color: '#0F2238' }}>{coFrom}</span> from COs &middot;{' '}
              <span style={{ fontWeight: 700, color: '#0F2238' }}>{coUnassigned}</span> with no CO assigned
            </div>
          ) : (
            <div>
              <span style={{ fontWeight: 700, color: '#0F2238' }}>{metaTotal}</span> CO requests in source
            </div>
          )}
          <div>Created Jan&ndash;Jul 2026 &middot; as of 22 Jul 2026</div>
        </div>
      </div>
    </div>
  );
}
