import './globals.css';
import NavBar from '@/app/components/NavBar';

export const metadata = {
  title: 'Chimera Cybersecurity',
  description: 'Security Operations Center',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        {/* One unified navbar for the whole app */}
        <NavBar />
        <main>{children}</main>
      </body>
    </html>
  );
}
