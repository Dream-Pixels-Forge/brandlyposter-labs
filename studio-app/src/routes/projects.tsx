import { createFileRoute } from '@tanstack/react-router';
import { ProjectsList } from '../components/ProjectsList';

export const Route = createFileRoute('/projects')({
  component: () => <ProjectsList />,
});