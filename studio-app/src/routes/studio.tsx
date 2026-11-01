import { createFileRoute } from '@tanstack/react-router';
import { PosterStudio } from '../components/PosterStudio';

export const Route = createFileRoute('/studio')({
  component: () => <PosterStudio />,
});