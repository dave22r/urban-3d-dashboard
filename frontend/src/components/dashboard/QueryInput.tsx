import { useState, KeyboardEvent } from "react";
import { Search, Loader2, Sparkles, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

interface QueryInputProps {
  onQuery: (query: string) => void;
  onClear: () => void;
  loading: boolean;
  hasFilters: boolean;
}

const EXAMPLE_QUERIES = [
  "show buildings over 100 meters",
  "find the tallest building",
  "buildings in the Beltline community",
  "buildings in the DC zoning under 10 million dollars",
  
];

export function QueryInput({ onQuery, onClear, loading, hasFilters }: QueryInputProps) {
  const [query, setQuery] = useState("");

  const handleSubmit = () => {
    if (query.trim()) {
      onQuery(query.trim());
    }
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter") {
      handleSubmit();
    }
  };

  const handleExampleClick = (example: string) => {
    setQuery(example);
    onQuery(example);
  };

  const handleClear = () => {
    setQuery("");
    onClear();
  };

  return (
    <div className="glass-panel rounded-xl p-4 space-y-4 animate-fade-in">
      <div className="flex items-center gap-2 mb-2">
        <Sparkles className="w-4 h-4 text-primary" />
        <h2 className="text-sm font-semibold text-foreground">AI Query</h2>
      </div>

      <div className="flex gap-2">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
          <Input
            type="text"
            placeholder="Ask about buildings... e.g. 'show buildings over 50 meters'"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={loading}
            className="pl-10 pr-10 bg-secondary/50 border-border/50 focus:border-primary/50 focus:ring-primary/20 placeholder:text-muted-foreground/60"
          />
          {query && (
            <button
              onClick={() => setQuery("")}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground transition-colors"
            >
              <X className="w-4 h-4" />
            </button>
          )}
        </div>
        
        <Button 
          onClick={handleSubmit} 
          disabled={loading || !query.trim()}
          className="bg-primary hover:bg-primary/90 text-primary-foreground font-medium px-6 shadow-glow"
        >
          {loading ? (
            <>
              <Loader2 className="w-4 h-4 mr-2 animate-spin" />
              Processing
            </>
          ) : (
            "Search"
          )}
        </Button>

        {hasFilters && (
          <Button
            onClick={handleClear}
            variant="outline"
            className="border-border/50 hover:bg-secondary/50"
          >
            Clear
          </Button>
        )}
      </div>

      {/* Example queries */}
      <div className="space-y-2">
        <p className="text-xs text-muted-foreground">Try these:</p>
        <div className="flex flex-wrap gap-2">
          {EXAMPLE_QUERIES.map((example) => (
            <button
              key={example}
              onClick={() => handleExampleClick(example)}
              disabled={loading}
              className="text-xs px-3 py-1.5 rounded-full bg-secondary/50 text-muted-foreground hover:bg-primary/20 hover:text-primary transition-all duration-200 disabled:opacity-50"
            >
              {example}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
