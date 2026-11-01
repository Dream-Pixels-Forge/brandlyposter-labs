import { createFileRoute } from '@tanstack/react-router';
import { SettingsPanel } from '../components/SettingsPanel';

export const Route = createFileRoute('/settings')({
  component: () => <SettingsPanel />,
});