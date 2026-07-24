import type { CSSProperties, ReactNode } from 'react';

export function Card({ children, style }: { children: ReactNode; style?: CSSProperties }) {
  return (
    <div
      style={{
        background: '#fff',
        border: '1px solid #E3E9EF',
        borderRadius: 10,
        padding: '20px 22px',
        ...style,
      }}
    >
      {children}
    </div>
  );
}
