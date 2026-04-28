import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Search, Eye, ChevronLeft, ChevronRight } from 'lucide-react';
import type { GoldenRecord } from '@/types';

interface GoldenRecordsTableProps {
  records: GoldenRecord[];
  onSelectRecord: (id: string) => void;
  searchQuery: string;
  onSearchChange: (query: string) => void;
}

export function GoldenRecordsTable({
  records,
  onSelectRecord,
  searchQuery,
  onSearchChange,
}: GoldenRecordsTableProps) {
  const [page, setPage] = useState(0);
  const pageSize = 10;
  const totalPages = Math.ceil(records.length / pageSize);
  const paginated = records.slice(page * pageSize, (page + 1) * pageSize);

  return (
    <Card className="col-span-2">
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle className="text-base font-semibold">Golden Records</CardTitle>
        <div className="relative w-64">
          <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search records..."
            value={searchQuery}
            onChange={(e) => { onSearchChange(e.target.value); setPage(0); }}
            className="pl-9 text-sm"
          />
        </div>
      </CardHeader>
      <CardContent>
        <div className="rounded-md border overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b bg-muted/50">
                  <th className="text-left p-3 font-medium">ID</th>
                  <th className="text-left p-3 font-medium">Name</th>
                  <th className="text-left p-3 font-medium">Email</th>
                  <th className="text-left p-3 font-medium">Company</th>
                  <th className="text-left p-3 font-medium">Region</th>
                  <th className="text-left p-3 font-medium">Ver</th>
                  <th className="text-left p-3 font-medium">Actions</th>
                </tr>
              </thead>
              <tbody>
                {paginated.map((record) => (
                  <tr key={record.id} className="border-b hover:bg-muted/50 transition-colors">
                    <td className="p-3 font-mono text-xs">{record.golden_record_id}</td>
                    <td className="p-3">
                      <div className="font-medium">
                        {record.canonical_first_name || ''} {record.canonical_last_name || ''}
                      </div>
                      {record.canonical_title && (
                        <div className="text-xs text-muted-foreground">{record.canonical_title}</div>
                      )}
                    </td>
                    <td className="p-3 text-xs">{record.canonical_email || '-'}</td>
                    <td className="p-3 text-xs">{record.canonical_company || '-'}</td>
                    <td className="p-3">
                      {record.canonical_region ? (
                        <Badge variant="outline" className="text-xs">
                          {record.canonical_region}
                        </Badge>
                      ) : (
                        '-'
                      )}
                    </td>
                    <td className="p-3">
                      <Badge variant="secondary" className="text-xs font-mono">
                        v{record.version}
                      </Badge>
                    </td>
                    <td className="p-3">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => onSelectRecord(record.golden_record_id)}
                        className="h-8 w-8 p-0"
                      >
                        <Eye className="h-4 w-4" />
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {records.length === 0 && (
            <div className="p-8 text-center text-muted-foreground">
              No golden records found
            </div>
          )}

          {totalPages > 1 && (
            <div className="flex items-center justify-between p-3 border-t">
              <span className="text-xs text-muted-foreground">
                Page {page + 1} of {totalPages} ({records.length} records)
              </span>
              <div className="flex gap-1">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setPage((p) => Math.max(0, p - 1))}
                  disabled={page === 0}
                  className="h-8 w-8 p-0"
                >
                  <ChevronLeft className="h-4 w-4" />
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setPage((p) => Math.min(totalPages - 1, p + 1))}
                  disabled={page >= totalPages - 1}
                  className="h-8 w-8 p-0"
                >
                  <ChevronRight className="h-4 w-4" />
                </Button>
              </div>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
