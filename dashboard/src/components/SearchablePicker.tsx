import { useMemo, useState } from "react";

export interface SearchablePickerItem {
  id: number;
  label: string;
  sublabel?: string;
}

interface SearchablePickerProps {
  items: SearchablePickerItem[];
  selectedId: number | null;
  onSelect: (id: number) => void;
  placeholder?: string;
  emptyMessage?: string;
  maxVisible?: number;
}

export function SearchablePicker({
  items,
  selectedId,
  onSelect,
  placeholder = "Search…",
  emptyMessage = "No matches.",
  maxVisible = 50,
}: SearchablePickerProps) {
  const [query, setQuery] = useState("");

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    const list = q
      ? items.filter(
          (item) =>
            item.label.toLowerCase().includes(q) ||
            item.sublabel?.toLowerCase().includes(q),
        )
      : items;
    return list.slice(0, maxVisible);
  }, [items, query, maxVisible]);

  const hiddenCount = useMemo(() => {
    const q = query.trim().toLowerCase();
    const total = q
      ? items.filter(
          (item) =>
            item.label.toLowerCase().includes(q) ||
            item.sublabel?.toLowerCase().includes(q),
        ).length
      : items.length;
    return Math.max(0, total - maxVisible);
  }, [items, query, maxVisible]);

  return (
    <div className="searchable-picker">
      <input
        type="search"
        className="searchable-picker-input"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder={placeholder}
        aria-label={placeholder}
      />
      {filtered.length === 0 ? (
        <p className="hint searchable-picker-empty">{emptyMessage}</p>
      ) : (
        <ul className="searchable-picker-list" role="listbox">
          {filtered.map((item) => (
            <li key={item.id}>
              <button
                type="button"
                role="option"
                aria-selected={selectedId === item.id}
                className={selectedId === item.id ? "selected" : undefined}
                onClick={() => onSelect(item.id)}
              >
                <span className="searchable-picker-label">{item.label}</span>
                {item.sublabel ? (
                  <span className="searchable-picker-sublabel">{item.sublabel}</span>
                ) : null}
              </button>
            </li>
          ))}
        </ul>
      )}
      {hiddenCount > 0 ? (
        <p className="hint">Refine search to see {hiddenCount} more.</p>
      ) : null}
    </div>
  );
}
