export function formatRouteName(routeName: string): string {
  if (routeName.endsWith(', The')) {
    return `The ${routeName.slice(0, -5)}`;
  }
  return routeName;
}