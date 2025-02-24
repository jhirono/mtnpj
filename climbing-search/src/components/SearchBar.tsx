interface SearchBarProps {
  onSearch: (query: string) => void
}

export function SearchBar({ onSearch }: SearchBarProps) {
  return (
    <div className="mb-6">
      <input
        type="text"
        placeholder="Search routes..."
        className="w-full px-4 py-2 border rounded-lg"
        onChange={(e) => onSearch(e.target.value)}
      />
    </div>
  )
} 