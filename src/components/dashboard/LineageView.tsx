import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Search, Loader2, ArrowLeft, GitMerge, Clock, History } from 'lucide-react';
import { useLineage } from '@/hooks/useApi';

interface LineageViewProps {
  goldenId?: string;
  onBack?: () => void;
}

export function LineageView({ goldenId, onBack }: LineageViewProps) {
  const [inputId, setInputId] = useState(goldenId || '');
  const [searchId, setSearchId] = useState(goldenId || '');

  const { data, loading, error } = useLineage(searchId);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    setSearchId(inputId.trim());
  };

  if (!searchId) {
    return (
      <Card className="col-span-2">
        <CardHeader>
          <CardTitle className="text-base font-semibold">Record Lineage</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSearch} className="flex gap-2">
            <Input
              placeholder="Enter Golden Record ID (e.g., GR-XXXX)"
              value={inputId}
              onChange={(e) => setInputId(e.target.value)}
              className="text-sm"
            />
            <Button type="submit" className="bg-blue-600 hover:bg-blue-700">
              <Search className="h-4 w-4" />
            </Button>
          </form>
          <div className="flex items-center justify-center h-[200px] text-muted-foreground text-sm">
            Search for a golden record to view its lineage
          </div>
        </CardContent>
      </Card>
    );
  }

  if (loading) {
    return (
      <Card className="col-span-2">
        <CardContent className="flex items-center justify-center h-[300px]">
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        </CardContent>
      </Card>
    );
  }

  if (error || !data) {
    return (
      <Card className="col-span-2">
        <CardHeader className="flex flex-row items-center gap-2">
          {onBack && (
            <Button variant="ghost" size="sm" onClick={onBack} className="h-8 w-8 p-0">
              <ArrowLeft className="h-4 w-4" />
            </Button>
          )}
          <CardTitle className="text-base font-semibold">Record Lineage</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSearch} className="flex gap-2 mb-4">
            <Input
              placeholder="Enter Golden Record ID"
              value={inputId}
              onChange={(e) => setInputId(e.target.value)}
              className="text-sm"
            />
            <Button type="submit" className="bg-blue-600 hover:bg-blue-700">
              <Search className="h-4 w-4" />
            </Button>
          </form>
          <div className="p-4 bg-red-50 rounded-lg text-sm text-red-600">
            {error || 'Record not found'}
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="col-span-2">
      <CardHeader className="flex flex-row items-center gap-2">
        {onBack && (
          <Button variant="ghost" size="sm" onClick={onBack} className="h-8 w-8 p-0">
            <ArrowLeft className="h-4 w-4" />
          </Button>
        )}
        <div className="flex-1">
          <CardTitle className="text-base font-semibold flex items-center gap-2">
            Record Lineage
            <Badge variant="secondary" className="font-mono text-xs">{data.golden_record_id}</Badge>
          </CardTitle>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Canonical Data */}
        <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
          <div className="p-3 bg-muted/50 rounded-lg">
            <div className="text-xs text-muted-foreground mb-1">Email</div>
            <div className="text-sm font-medium truncate">{data.canonical_data?.email || '-'}</div>
          </div>
          <div className="p-3 bg-muted/50 rounded-lg">
            <div className="text-xs text-muted-foreground mb-1">Phone</div>
            <div className="text-sm font-medium">{data.canonical_data?.phone || '-'}</div>
          </div>
          <div className="p-3 bg-muted/50 rounded-lg">
            <div className="text-xs text-muted-foreground mb-1">Company</div>
            <div className="text-sm font-medium truncate">{data.canonical_data?.company || '-'}</div>
          </div>
          <div className="p-3 bg-muted/50 rounded-lg">
            <div className="text-xs text-muted-foreground mb-1">Name</div>
            <div className="text-sm font-medium">
              {data.canonical_data?.first_name || ''} {data.canonical_data?.last_name || ''}
            </div>
          </div>
          <div className="p-3 bg-muted/50 rounded-lg">
            <div className="text-xs text-muted-foreground mb-1">Title</div>
            <div className="text-sm font-medium">{data.canonical_data?.title || '-'}</div>
          </div>
          <div className="p-3 bg-muted/50 rounded-lg">
            <div className="text-xs text-muted-foreground mb-1">Region</div>
            <div className="text-sm font-medium">{data.canonical_data?.region || '-'}</div>
          </div>
        </div>

        {/* Provenance */}
        <div className="p-4 border rounded-lg">
          <h4 className="text-sm font-semibold mb-3 flex items-center gap-2">
            <GitMerge className="h-4 w-4" />
            Provenance
          </h4>
          <div className="text-xs text-muted-foreground mb-2">
            Source Records: {data.provenance?.source_record_ids?.length || 0}
          </div>
          <div className="flex flex-wrap gap-1">
            {data.provenance?.source_record_ids?.map((id) => (
              <Badge key={id} variant="outline" className="text-xs font-mono">
                {id}
              </Badge>
            )) || (
              <span className="text-xs text-muted-foreground">No source records</span>
            )}
          </div>
        </div>

        {/* Events */}
        {data.history?.events && data.history.events.length > 0 && (
          <div className="p-4 border rounded-lg">
            <h4 className="text-sm font-semibold mb-3 flex items-center gap-2">
              <History className="h-4 w-4" />
              Merge Events
            </h4>
            <div className="space-y-2">
              {data.history.events.map((event: Record<string, unknown>, idx: number) => (
                <div key={idx} className="flex items-start gap-3 p-2 bg-muted/30 rounded">
                  <Badge variant="outline" className="text-xs mt-0.5">
                    {String(event.event_type || 'unknown')}
                  </Badge>
                  <div className="text-xs">
                    <div className="font-medium">Event ID: {String(event.event_id || 'N/A')}</div>
                    <div className="text-muted-foreground">
                      Confidence: {typeof event.confidence_at_merge === 'number' ? event.confidence_at_merge.toFixed(4) : 'N/A'}
                    </div>
                    <div className="text-muted-foreground">
                      {event.created_at ? new Date(String(event.created_at)).toLocaleString() : '-'}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Audit Trail */}
        <div className="p-4 border rounded-lg">
          <h4 className="text-sm font-semibold mb-3 flex items-center gap-2">
            <Clock className="h-4 w-4" />
            Audit Trail
          </h4>
          <div className="grid grid-cols-3 gap-4 text-center">
            <div>
              <div className="text-lg font-bold">{data.audit_trail?.version_count || 0}</div>
              <div className="text-xs text-muted-foreground">Versions</div>
            </div>
            <div>
              <div className="text-lg font-bold">{data.audit_trail?.event_count || 0}</div>
              <div className="text-xs text-muted-foreground">Events</div>
            </div>
            <div>
              <div className="text-lg font-bold">{data.audit_trail?.survivorship_decision_count || 0}</div>
              <div className="text-xs text-muted-foreground">Survivorship Decisions</div>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
