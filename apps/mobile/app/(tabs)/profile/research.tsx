// Moved to insights/research.tsx — redirect for any saved deep links
import { Redirect } from 'expo-router';
export default function ResearchRedirect() {
  return <Redirect href="/(tabs)/insights/research" />;
}
