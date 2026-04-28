import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import type { MatchResult } from '@/types';

interface MatchesTableProps {
  matches: MatchResult[];
}

function getStatusBadge(status: string) {
  if (status === 'auto_merge') return <Badge className="bg-emerald-100 text-emerald-700">Auto Merge</Badge>;
  if (status === 'review') return <Badge className="bg-amber-100 text-amber-700">Review</Badge>;
  if (status === 'distinct') return <Badge variant="secondary">Distinct</Badge>;
  return <Badge variant="outline">{status}</Badge>;
}

function getTierBadge(tier: string) {
  if (tier === 'tier_a') return <Badge variant="outline" className="text-xs">Tier A</Badge>;
  if (tier === 'tier_b_pending') return <Badge variant="outline" className="text-xs text-amber-600 border-amber-300">Tier B</Badge>;
  return null;
}

export function MatchesTable({ matches }: MatchesTableProps) {
  const [activeTab, setActiveTab] = useState('all');

  const filtered = activeTab === 'all'
    ? matches
    : matches.filter((m) => m.match_status === activeTab);

  const counts = {
    all: matches.length,
    auto_merge: matches.filter((m) => m.match_status === 'auto_merge').length,
    review: matches.filter((m) => m.match_status === 'review').length,
    distinct: matches.filter((m) => m.match_status === 'distinct').length,
  };

  return (
    <Card className="col-span-2">
      <CardHeader>
        <CardTitle className="text-base font-semibold">Recent Match Results</CardTitle>
      </CardHeader>
      <CardContent>
        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList className="mb-4">
            <TabsTrigger value="all">All ({counts.all})</TabsTrigger>
            <TabsTrigger value="auto_merge">Auto Merge ({counts.auto_merge})</TabsTrigger>
            <TabsTrigger value="review">Review ({counts.review})</TabsTrigger>
            <TabsTrigger value="distinct">Distinct ({counts.distinct})</TabsTrigger>
          </TabsList>

          <TabsContent value={activeTab}>
            <div className="rounded-md border overflow-hidden">
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b bg-muted/50">
                      <th className="text-left p-3 font-medium">Status</th>
                      <th className="text-left p-3 font-medium">Confidence</th>
                      <th className="text-left p-3 font-medium">Email</th>
                      <th className="text-left p-3 font-medium">Name</th>
                      <th className="text-left p-3 font-medium">Phone</th>
                      <th className="text-left p-3 font-medium">Block</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filtered.slice(0, 20).map((match) => (
                      <tr key={match.id} className="border-b hover:bg-muted/50 transition-colors">
                        <td className="p-3">
                          <div className="flex flex-col gap-1">
                            {getStatusBadge(match.match_status)}
                            {getTierBadge(match.match_tier)}
                          </div>
                        </td>
                        <td className="p-3">
                          <div className="flex items-center gap-2">
                            <div className="w-16 h-2 bg-gray-200 rounded-full overflow-hidden">
                              <div
                                className="h-full rounded-full transition-all"
                                style={{
                                  width: `${match.confidence_score * 100}%`,
                                  backgroundColor:
                                    match.confidence_score >= 0.85
                                      ? '#10b981'
                                      : match.confidence_score >= 0.6
                                      ? '#f59e0b'
                                      : '#6b7280',
                                }}
                              />
                            </div>
                            <span className="text-xs font-mono">
                              {match.confidence_score.toFixed(3)}
                            </span>
                          </div>
                        </td>
                        <td className="p-3">
                          <div className="text-xs">
                            <div>{match.email_exact ? 'Yes' : 'No'} exact</div>
                            <div>{match.email_domain ? 'Yes' : 'No'} domain</div>
                          </div>
                        </td>
                        <td className="p-3">
                          <span className="font-mono text-xs">
                            {match.name_jaro_winkler.toFixed(3)}
                          </span>
                        </td>
                        <td className="p-3">
                          <span className="text-xs">
                            {match.phone_exact ? 'Yes' : 'No'}
                          </span>
                        </td>
                        <td className="p-3">
                          <Badge variant="outline" className="text-xs">
                            {match.block_type}
                          </Badge>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              {filtered.length === 0 && (
                <div className="p-8 text-center text-muted-foreground">
                  No matches in this category
                </div>
              )}
            </div>
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  );
}
